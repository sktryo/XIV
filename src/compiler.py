# xiv_compiler.py
import re
import os
import html
import logging
from typing import Set, Dict, Optional, cast
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

    def compile(self, main_file_path: str, templates_dir: str) -> str:
        """
        指定されたメインのXIVファイルをコンパイルし、テンプレートを解決してHTMLを生成します。

        Args:
            main_file_path (str): メインのXIVファイルへのパス。
            templates_dir (str): テンプレートファイルが保存されているディレクトリへのパス。

        Returns:
            str: コンパイルされたHTML文字列。

        Raises:
            FileNotFoundError: 指定されたXIVファイルまたはテンプレートディレクトリが見つからない場合。
            ValueError: 無効なパスが指定された場合。
            CompilerError: コンパイル中に致命的なエラーが発生した場合。
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

        processed_main_content: str = self._process_content(main_content_raw, templates_dir, "main.xiv")

        final_html: str = re.sub(r'<xiv type="main">(.*?)</xiv>', r'\1', processed_main_content, flags=re.DOTALL)

        final_output: str = f"""<!DOCTYPE html>
<html>
{final_html}
</html>"""

        return BeautifulSoup(final_output, "lxml").prettify()

    def _process_content(self, current_content: str, templates_dir: str, current_template_context_path: str) -> str:
        # コメントの削除
        current_content = re.sub(r'<!--xiv-comment-->', '', current_content)

        soup: BeautifulSoup = BeautifulSoup(current_content, 'lxml')

        for match in soup.find_all('x-temp'):
            assert isinstance(match, Tag)
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

            template_args: Dict[str, str] = {}
            for attr, value in match.attrs.items():
                if attr.startswith('t-'):
                    key: str = attr[2:]
                    value_str: str = str(value)
                    value_escaped: str = html.escape(value_str, quote=True)
                    template_args[key] = value_escaped

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
            processed_nested_template_content: str = self._process_content(template_to_process, templates_dir, referenced_template_full_path)
            self._visited_templates_stack.remove(referenced_template_full_path)

            final_template_html: str = processed_nested_template_content
            for arg_key, arg_value in template_args.items():
                placeholder: str = f"{{{{{arg_key}}}}}"
                final_template_html = final_template_html.replace(placeholder, arg_value)
            
            # デフォルト値の処理
            def replace_default(match):
                full_placeholder = match.group(0)
                placeholder_name = match.group(1)
                default_value = match.group(2) if match.group(2) else ''
                
                # 既に置換された引数は除外
                if placeholder_name in template_args:
                    return template_args[placeholder_name]
                else:
                    return default_value
            
            final_template_html = re.sub(r'{{([^}|]+)(?:\|([^}]*))?}}', replace_default, final_template_html)

            safe_template_name: str = re.sub(r'[^\w-]', '', template_name)
            replacement_div = soup.new_tag('div', attrs={'class': f'x-{safe_template_name}'})
            replacement_div.append(BeautifulSoup(final_template_html.strip(), 'lxml'))
            
            match.replace_with(replacement_div)

        return str(soup)