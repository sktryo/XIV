# main.py
import os
import argparse
from compiler import XivCompiler # クラスとしてインポート

def main():
    parser = argparse.ArgumentParser(
        description="XIVテンプレート言語をHTMLにコンパイルします。",
        formatter_class=argparse.RawTextHelpFormatter # ヘルプテキストの改行を有効にする
    )
    parser.add_argument(
        "input_file",
        help="コンパイルするメインのXIVファイルのパス。\n例: python main.py main.xiv"
    )
    parser.add_argument(
        "-t", "--templates_dir",
        default=os.path.join(os.getcwd(), "templates"),
        help="テンプレートファイルが格納されているディレクトリのパス (デフォルト: ./templates)"
    )
    parser.add_argument(
        "-o", "--output_file",
        default=os.path.join(os.getcwd(), "index.html"),
        help="コンパイルされたHTMLの出力先ファイルパス (デフォルト: ./index.html)"
    )

    args = parser.parse_args()

    main_xiv_file = args.input_file
    templates_dir = args.templates_dir
    output_file = args.output_file

    # コンパイラのインスタンスを作成
    compiler = XivCompiler()

    print(f"\n--- XIVコンパイルを開始します ---")
    print(f"  入力ファイル: {main_xiv_file}")
    print(f"  テンプレートディレクトリ: {templates_dir}")
    print(f"  出力ファイル: {output_file}")

    try:
        compiled_html_output = compiler.compile(main_xiv_file, templates_dir)

        # 出力ディレクトリが存在しない場合は作成
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(compiled_html_output)
        print(f"\n✅ コンパイルが正常に完了しました。結果は '{output_file}' に保存されました。")
        print("\n--- コンパイル結果プレビュー (最初の500文字) ---")
        print(compiled_html_output[:500] + "..." if len(compiled_html_output) > 500 else compiled_html_output)

    except (FileNotFoundError, ValueError, Exception) as e:
        print(f"\n❌ コンパイル中にエラーが発生しました: {e}")
        print("エラーが発生したため、出力ファイルは生成されませんでした。")

if __name__ == "__main__":
    main()
