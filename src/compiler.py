# xiv_compiler.py
import re
import os
import html
import json
import copy
import logging
from typing import Set, Dict, Optional, cast, Any, List
from bs4 import BeautifulSoup
from bs4.element import Tag

class CompilerError(Exception):
    """ XIVコンパイラに固有のエラーのためのカスタム例外クラス """
    def __init__(self, message: str, template_name: Optional[str] = None):
        super().__init__(message)
        self.template_name = template_name

class XivCompiler:
    """
    XIVファイルをHTMLにコンパイルするためのクラス。
    テンプレートのネスト、循環参照の検出、HTMLエスケープをサポートします。
    """
    def __init__(self) -> None:
        """
        コンパイラの新しいインスタンスを初期化します。
        このインスタンスは、現在のコンパイルセッションで訪問したテンプレートのパスを追跡します。
        """
        self._visited_templates_stack: Set[str] = set()

    def _get_value_from_path(self, path: str, data: Dict[str, Any]) -> Any:
        """ ドット記法のパスを使って、ネストした辞書から値を取得します。 """
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value

    def _evaluate_condition(self, condition_str: str, args: Dict[str, Any]) -> bool:
        """ 条件式を評価して真偽値を返します。 """
        is_negated = condition_str.startswith('not ')
        var_name = condition_str[4:].strip() if is_negated else condition_str.strip()

        value = self._get_value_from_path(var_name, args)

        if value is None:
            is_true = False
        elif isinstance(value, bool):
            is_true = value
        elif str(value).lower() in ["false", "0", ""]:
            is_true = False
        else:
            is_true = True
            
        return not is_true if is_negated else is_true

    def compile(self, main_file_path: str, templates_dir: str) -> str:
        """
        指定されたメインのXIVファイルをコンパイルし、テンプレートを解決してHTMLを生成します。
        """
        self._visited_templates_stack = set()

        main_file_path = os.path.normpath(main_file_path)
        templates_dir = os.path.normpath(templates_dir)

        if not os.path.exists(main_file_path):
            raise FileNotFoundError(f"エラー: メインのXIVファイルが見つかりません: {main_file_path}")
        if not os.path.isfile(main_file_path):
            raise ValueError(f"エラー: メインのXIVファイルはファイルではありません: {main_file_path}")

        if not os.path.exists(templates_dir):
            raise FileNotFoundError(f"エラー: テンプレートディレクトリが見つかりません: {templates_dir}")
        if not os.path.isdir(templates_dir):
            raise ValueError(f"エラー: テンプレートディレクトリはディレクトリではありません: {templates_dir}")

        try:
            with open(main_file_path, 'r', encoding='utf-8') as f:
                main_content_raw: str = f.read()
        except Exception as e:
            raise CompilerError(f"メインのXIVファイルの読み込み中にエラーが発生しました: {e}")

        processed_main_content: str = self._process_content(main_content_raw, templates_dir, "main.xiv", {})

        # Inject the runtime script
        try:
            # Get the directory of the current script (src/compiler.py)
            compiler_dir = os.path.dirname(os.path.abspath(__file__))
            runtime_path = os.path.join(compiler_dir, 'runtime', 'xiv.js')
            with open(runtime_path, 'r', encoding='utf-8') as f:
                runtime_script = f.read()
        except FileNotFoundError:
            runtime_script = "// XIV Runtime not found.インタラクティブ機能は動作しません。"

        soup = BeautifulSoup(processed_main_content, 'lxml')
        
        # Find the main xiv tag to inject script and content
        main_tag = soup.find('xiv', {'type': 'main'})
        if main_tag:
            script_tag = soup.new_tag("script")
            script_tag.string = runtime_script
            main_tag.append(script_tag)
            main_tag.unwrap()

        final_output: str = f"""<!DOCTYPE html>
<html>
{str(soup)}
</html>"""

        return BeautifulSoup(final_output, "lxml").prettify()

    def _process_content(self, current_content: str, templates_dir: str, current_template_context_path: str, args: Dict[str, Any]) -> str:
        current_content = re.sub(r'<!--xiv-comment-->', '', current_content)

        soup: BeautifulSoup = BeautifulSoup(current_content, 'lxml')

        # --- Process directives in the correct order: for -> if -> temp ---

        # 1. Process x-for
        for element in soup.find_all(attrs={"x-for": True}):
            loop_expr = element.get('x-for')
            del element['x-for']

            match_expr = re.match(r'^\s*(\w+)\s+in\s+([\w.]+)\s*$', loop_expr)
            if not match_expr:
                raise CompilerError(f"Invalid x-for expression: '{loop_expr}'", current_template_context_path)

            item_var, items_var = match_expr.groups()
            
            items_data_source = self._get_value_from_path(items_var, args)
            
            items_data: List[Any]
            if items_data_source is None:
                items_data = []
            elif isinstance(items_data_source, str):
                try:
                    items_data = json.loads(items_data_source)
                except json.JSONDecodeError:
                    raise CompilerError(f"Invalid JSON data for '{items_var}' in x-for: {items_data_source}", current_template_context_path)
            elif isinstance(items_data_source, list):
                items_data = items_data_source
            else:
                raise CompilerError(f"Data for '{items_var}' in x-for must be a list or a JSON string.", current_template_context_path)

            if not isinstance(items_data, list):
                raise CompilerError(f"Data for '{items_var}' in x-for must be a list.", current_template_context_path)

            generated_elements = []
            for item_data in items_data:
                loop_args = copy.deepcopy(args)
                loop_args[item_var] = item_data
                
                template_element = copy.copy(element)
                processed_item_html = self._process_content(str(template_element), templates_dir, current_template_context_path, loop_args)
                processed_soup = BeautifulSoup(processed_item_html, 'lxml')
                generated_elements.extend(processed_soup.body.contents if processed_soup.body else processed_soup.contents)

            element.replace_with(*generated_elements)

        # 2. Process x-if
        for element in soup.find_all(attrs={"x-if": True}):
            condition_str = element.get('x-if')
            if isinstance(condition_str, str):
                del element['x-if']
                if not self._evaluate_condition(condition_str, args):
                    element.decompose()

        # 3. Process x-temp
        for match in soup.find_all('x-temp'):
            assert isinstance(match, Tag)

            slot_content_html: str = "".join(str(c) for c in match.contents)
            processed_slot_html: str = self._process_content(slot_content_html, templates_dir, current_template_context_path, args)

            template_name: Optional[str] = cast(str, match.get('x-name'))
            
            if not template_name:
                raise CompilerError(f"<x-temp> タグに必須の x-name 属性がありません。", current_template_context_path)

            referenced_template_full_path: str = os.path.normpath(os.path.join(templates_dir, f"{template_name}.xiv"))

            if referenced_template_full_path in self._visited_templates_stack:
                raise CompilerError(f"循環参照が検出されました: '{current_template_context_path}' -> '{template_name}.xiv'", current_template_context_path)

            if not referenced_template_full_path.startswith(templates_dir + os.sep) and referenced_template_full_path != templates_dir:
                raise CompilerError(f"不正なテンプレートパスです: '{template_name}.xiv'。ディレクトリトラバーサルは許可されていません。", current_template_context_path)

            if not os.path.isfile(referenced_template_full_path):
                raise FileNotFoundError(f"テンプレートファイルが見つかりません: {referenced_template_full_path}") from None

            new_args: Dict[str, Any] = {}
            for attr, value in match.attrs.items():
                if attr.startswith('t-'):
                    key: str = attr[2:]
                    value_str: str = str(value)
                    new_args[key] = value_str

            try:
                with open(referenced_template_full_path, 'r', encoding='utf-8') as f:
                    template_content_raw: str = f.read()
            except Exception as e:
                raise CompilerError(f"テンプレートファイル '{referenced_template_full_path}' の読み込み中にエラーが発生しました: {e}", current_template_context_path)

            template_inner_content_match: Optional[re.Match[str]] = re.search(r'<xiv type="template">(.*?)</xiv>', template_content_raw, re.DOTALL)
            if template_inner_content_match:
                template_to_process: str = template_inner_content_match.group(1)
            else:
                template_to_process = template_content_raw

            self._visited_templates_stack.add(referenced_template_full_path)
            processed_nested_template_content: str = self._process_content(template_to_process, templates_dir, referenced_template_full_path, new_args)
            self._visited_templates_stack.remove(referenced_template_full_path)

            template_soup = BeautifulSoup(processed_nested_template_content, 'lxml')
            slot_tag = template_soup.find('x-slot')
            if slot_tag:
                slot_soup = BeautifulSoup(processed_slot_html, 'lxml')
                slot_contents = slot_soup.body.contents if slot_soup.body else slot_soup.contents
                slot_tag.replace_with(*slot_contents)
            
            final_template_html = str(template_soup)

            safe_template_name: str = re.sub(r'[^\w-]', '', template_name)
            replacement_div = soup.new_tag('div', attrs={'class': f'x-{safe_template_name}'})
            
            final_soup = BeautifulSoup(final_template_html, 'lxml')
            contents = final_soup.body.contents if final_soup.body else final_soup.contents
            replacement_div.extend(contents)
            
            match.replace_with(replacement_div)

        # 4. Final placeholder substitution
        content_after_directives = str(soup)

        def replacer(m):
            key = m.group(1).strip()
            default_value = m.group(2).strip() if m.group(2) is not None else ''
            
            value = self._get_value_from_path(key, args)

            if value is not None:
                return html.escape(str(value), quote=True)
            else:
                return html.escape(default_value, quote=True)

        final_content = re.sub(r'{{\s*([^}|]+?)\s*(?:\|([^}]*))?}}', replacer, content_after_directives)

        return final_content