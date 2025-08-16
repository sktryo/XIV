# xiv_compiler.py
import re
import os
import html # HTMLエスケープのために追加

class XivCompiler:
    """
    XIVファイルをHTMLにコンパイルするためのクラス。
    テンプレートのネスト、循環参照の検出、HTMLエスケープをサポートします。
    """
    def __init__(self):
        """
        コンパイラの新しいインスタンスを初期化します。
        このインスタンスは、現在のコンパイルセッションで訪問したテンプレートのパスを追跡します。
        """
        self._visited_templates_stack = set()

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
            Exception: その他のコンパイルエラーが発生した場合。
        """
        # 新しいコンパイルセッションの開始時にスタックをリセットします。
        self._visited_templates_stack = set()

        # パスの正規化と存在チェック
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
                main_content_raw = f.read()
        except Exception as e:
            raise Exception(f"メインのXIVファイルの読み込み中にエラーが発生しました: {e}")

        # メインコンテンツの処理を開始します。この関数が再帰的にテンプレートを解決します。
        # "main.xiv"というパスは、エラーメッセージ用であり、実際のファイルパスではありません。
        processed_main_content = self._process_content(main_content_raw, templates_dir, "main.xiv")

        # 最終的なHTML構造の生成
        final_html = re.sub(r'<xiv type="main">(.*?)</xiv>', r'\1', processed_main_content, flags=re.DOTALL)

        # 余分な空白行を削除し、HTMLフォーマットをきれいにします。
        cleaned_lines = []
        for line in final_html.splitlines():
            stripped_line = line.strip()
            # 空行、またはhead/bodyタグのみの行でない場合にのみ追加
            # タグの前後にあるスペースも考慮して保持
            if stripped_line or re.match(r'^\s*<(/)?(head|body)[^>]*>$', line):
                cleaned_lines.append(line)
        final_html = "\n".join(cleaned_lines).strip() # 最後にも全体をトリム

        final_output = f"""<!DOCTYPE html>
<html>
{final_html}
</html>"""

        return final_output

    def _process_content(self, current_content: str, templates_dir: str, current_template_context_path: str) -> str:
        """
        現在のコンテンツ文字列内の <x-temp> タグを再帰的に処理します。
        この関数は、コンテンツを解析し、必要に応じて自身を再帰的に呼び出します。

        Args:
            current_content (str): 現在処理しているHTML/XIVコンテンツ文字列。
            templates_dir (str): テンプレートファイルが保存されているディレクトリへのパス。
            current_template_context_path (str): 現在処理中のテンプレートの論理的なパス（エラーメッセージ用）。

        Returns:
            str: 処理され、解決されたHTMLコンテンツ文字列。
        """
        parts = []
        last_end = 0

        # <x-temp ... /> タグをすべて検索
        x_temp_matches = list(re.finditer(r'<x-temp\s+x-name="([^"]+)"([^>]*?)/?\s*>', current_content, re.DOTALL))

        for match in x_temp_matches:
            # 現在の <x-temp> タグの前のコンテンツを追加
            parts.append(current_content[last_end:match.start()])

            full_tag = match.group(0)           # 例: <x-temp x-name="header" t-string="LOL" />
            template_name = match.group(1)      # 例: "header"
            attributes_str = match.group(2)     # 例: ' t-string="LOL"'

            # 参照されるテンプレートのフルパスを構築 (拡張子は .xiv)
            referenced_template_full_path = os.path.normpath(os.path.join(templates_dir, f"{template_name}.xiv"))

            # --- 循環参照の検出 ---
            # 参照しようとしているテンプレートが、既に現在の呼び出しスタックに含まれている場合
            if referenced_template_full_path in self._visited_templates_stack:
                print(f"警告: 循環参照が検出されました。'{current_template_context_path}' からテンプレート '{template_name}' を参照しようとしましたが、'{template_name}' は既に上位で処理中です。この参照はスキップされ、元のタグが保持されます。")
                parts.append(full_tag) # 無限ループを防ぐため、元のタグをそのまま保持
                last_end = match.end()
                continue # このテンプレートの処理をスキップ

            # --- パスの検証 (セキュリティ対策: パス横断攻撃の防止) ---
            # 参照されるテンプレートが templates_dir の内部にあることを厳密に確認します。
            # os.sep はOSごとのパス区切り文字（Windowsでは'\\', Unix/Linuxでは'/'）
            if not referenced_template_full_path.startswith(templates_dir + os.sep) and referenced_template_full_path != templates_dir:
                print(f"警告: 不正なテンプレートパスの試行を検出しました: {template_name}.xiv。これは許可されていません。元のタグが保持されます。")
                parts.append(full_tag)
                last_end = match.end()
                continue

            # --- テンプレートファイルの存在チェック ---
            if not os.path.exists(referenced_template_full_path) or not os.path.isfile(referenced_template_full_path):
                print(f"エラー: テンプレートファイルが見つからないか、ファイルではありません: {referenced_template_full_path}。元のタグが保持されます。")
                parts.append(full_tag)
                last_end = match.end()
                continue

            # --- テンプレート引数の解析とHTMLエスケープ ---
            template_args = {}
            for attr_match in re.finditer(r't-([\w-]+)="([^"]*)"', attributes_str):
                key = attr_match.group(1)
                # 取得した値はHTMLエスケープしてXSSを防止
                value = html.escape(attr_match.group(2))
                template_args[key] = value

            try:
                with open(referenced_template_full_path, 'r', encoding='utf-8') as f:
                    template_content_raw = f.read()
            except Exception as e:
                print(f"エラー: テンプレートファイル '{referenced_template_full_path}' の読み込み中にエラーが発生しました: {e}。元のタグが保持されます。")
                parts.append(full_tag)
                last_end = match.end()
                continue

            # テンプレートファイルから <xiv type="template"> タグの中身だけを抽出
            template_inner_content_match = re.search(r'<xiv type="template">(.*?)</xiv>', template_content_raw, re.DOTALL)
            template_to_process = template_inner_content_match.group(1) if template_inner_content_match else template_content_raw

            # --- 再帰呼び出しの前にスタックに追加 ---
            # 現在処理中のテンプレートをスタックに追加します。
            self._visited_templates_stack.add(referenced_template_full_path)

            # --- 再帰呼び出し: ロードしたテンプレートのコンテンツを処理 ---
            # ここでネストされたテンプレートが処理されます。
            processed_nested_template_content = self._process_content(template_to_process, templates_dir, referenced_template_full_path)

            # --- 再帰呼び出しから戻った後にスタックから削除 ---
            # テンプレートの処理が完了したら、スタックから削除します。
            self._visited_templates_stack.remove(referenced_template_full_path)

            # --- 処理されたネストされたコンテンツ内のプレースホルダーを置換 ---
            final_template_html = processed_nested_template_content
            for arg_key, arg_value in template_args.items():
                placeholder = f"{{{{{arg_key}}}}}" # 例: {{string}}
                final_template_html = final_template_html.replace(placeholder, arg_value)

            # 最終的なHTMLとして、置換されたテンプレートコンテンツを div で囲みます。
            # クラス名は "x-<テンプレート名>" の形式にします。
            safe_template_name = re.sub(r'[^\w-]', '', template_name) # クラス名として安全な名前にサニタイズ
            replacement_html = f'<div class="x-{safe_template_name}">{final_template_html.strip()}</div>'
            parts.append(replacement_html)

            last_end = match.end()

        # 最後の <x-temp> タグの後のコンテンツを追加します。
        parts.append(current_content[last_end:])

        # 処理されたコンテンツ文字列を返します。
        return "".join(parts)
