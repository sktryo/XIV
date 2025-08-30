# XIV

XIVは、HTMLテンプレートをコンポーネントベースで記述し、単一のHTMLファイルにコンパイルするためのシンプルなテンプレートエンジンです。

## 特徴

- **コンポーネントベース:** `<x-temp>` タグを使って、テンプレートを部品として再利用できます。
- **引数渡し:** `t-*` 属性を介して、コンポーネントに文字列を渡すことができます。
- **ネスト:** コンポーネントの中に、さらに別のコンポーネントを配置できます。
- **循環参照の検出:** テンプレート同士が無限にお互いを呼び出すような状況を検出し、コンパイルを停止します。
- **安全性:** パストラバーサル攻撃の防止や、属性値のエスケープに関するルールを設けています。

## インストール

まず、リポジトリをクローンし、必要なライブラリをインストールします。

```shell
# 仮想環境があることを確認してください
# pip install -r requirements.txt
venv/bin/pip install -r requirements.txt
```

## 使い方

`main.py` を使って `.xiv` ファイルをコンパイルします。

```shell
python3 main.py [入力ファイル] [オプション]
```

**コマンドラインオプション:**

```
usage: main.py [-h] [-t TEMPLATES_DIR] [-o OUTPUT_FILE] input_file

XIVテンプレート言語をHTMLにコンパイルします。

positional arguments:
  input_file            コンパイルするメインのXIVファイルのパス。
                        例: python main.py main.xiv

options:
  -h, --help            show this help message and exit
  -t TEMPLATES_DIR, --templates_dir TEMPLATES_DIR
                        テンプレートファイルが格納されているディレクトリのパス (デフォルト: ./templates)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        コンパイルされたHTMLの出力先ファイルパス (デフォルト: ./index.html)
```

## 構文ガイド

### コンポーネント (`<x-temp>`)

他のテンプレートファイルを読み込むには、`<x-temp>` タグを使用します。
`x-name` 属性で、`templates` ディレクトリにあるテンプレートファイル（`.xiv`拡張子を除く）の名前を指定します。

```html
<!-- main.xiv -->
<x-temp x-name="panel" />
```

### 引数 (`t-*` 属性)

`t-` から始まる属性を使うことで、コンポーネントにデータを渡すことができます。

```html
<!-- main.xiv -->
<x-temp x-name="panel" t-title="ようこそ" t-message="こんにちは、世界！" />
```

テンプレートファイル側では、`{{}}` で囲むことで、渡された値を受け取ります。

```html
<!-- templates/panel.xiv -->
<xiv type="template">
    <h2>{{title}}</h2>
    <p>{{message}}</p>
</xiv>
```

### 【重要】属性値のエスケープ

`t-*` 属性の値に `"` や `<` などの特殊文字を含める場合は、**必ずHTMLエスケープを行う必要があります**。これはXSS（クロスサイトスクリプティング）脆弱性を防ぐために重要です。

**悪い例 (不正な形式):**
```html
<x-temp x-name="comment" t-text="<script>alert("XSS")</script>" />
```

**良い例 (正しい形式):**
```html
<x-temp x-name="comment" t-text="&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;" />
```

コンパイラは、ユーザーが提供したエスケープ済みの文字列をそのままHTMLに出力します。

## ライセンス

このプロジェクトは [LICENSE](./LICENSE) の下で公開されています。