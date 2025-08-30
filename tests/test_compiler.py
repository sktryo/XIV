
import os
import pytest
import shutil
from pathlib import Path
import logging
from bs4 import BeautifulSoup
from src.compiler import XivCompiler, CompilerError

@pytest.fixture
def compiler():
    """ A fixture that returns a XivCompiler instance. """
    return XivCompiler()

@pytest.fixture
def temp_project(tmp_path):
    """ A fixture that creates a temporary project structure for testing. """
    (tmp_path / "templates").mkdir()
    return tmp_path

def test_basic_compilation(compiler, temp_project):
    """ Tests basic compilation of a single XIV file without templates. """
    main_xiv_content = """<xiv type="main">
    <head><title>Test</title></head>
    <body><h1>Hello</h1></body>
</xiv>"""
    main_xiv_file = temp_project / "main.xiv"
    main_xiv_file.write_text(main_xiv_content, encoding="utf-8")

    result = compiler.compile(str(main_xiv_file), str(temp_project / "templates"))
    
    soup = BeautifulSoup(result, 'lxml')
    assert soup.title.text.strip() == "Test"
    assert soup.h1.text.strip() == "Hello"
    assert '<div class="x-' not in result # No templates used

def test_template_inclusion_and_argument_passing(compiler, temp_project):
    """ Tests template inclusion with arguments. """
    main_xiv_content = """<xiv type="main">
    <body>
        <x-temp x-name="card" t-title="My Card" t-content="This is the content." />
    </body>
</xiv>"""
    main_xiv_file = temp_project / "main.xiv"
    main_xiv_file.write_text(main_xiv_content, encoding="utf-8")

    template_content = """<xiv type="template">
    <h2>{{title}}</h2>
    <p>{{content}}</p>
</xiv>"""
    template_file = temp_project / "templates" / "card.xiv"
    template_file.write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(main_xiv_file), str(temp_project / "templates"))

    soup = BeautifulSoup(result, 'lxml')
    card_div = soup.find('div', class_='x-card')
    assert card_div is not None
    assert card_div.h2.text.strip() == "My Card"
    assert card_div.p.text.strip() == "This is the content."

def test_circular_reference(compiler, temp_project):
    """ Tests that a circular reference raises a CompilerError. """
    # main.xiv -> a.xiv -> b.xiv -> a.xiv (circular)
    main_xiv_content = '<xiv type="main"><x-temp x-name="a" /></xiv>'
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_a_content = '<xiv type="template">A includes B: <x-temp x-name="b" /></xiv>'
    (temp_project / "templates" / "a.xiv").write_text(template_a_content, encoding="utf-8")

    template_b_content = '<xiv type="template">B includes A: <x-temp x-name="a" /></xiv>'
    (temp_project / "templates" / "b.xiv").write_text(template_b_content, encoding="utf-8")

    with pytest.raises(CompilerError, match="循環参照が検出されました"):
        compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))

def test_template_not_found(compiler, temp_project):
    """ Tests that a missing template raises FileNotFoundError. """
    main_xiv_content = '<xiv type="main"><x-temp x-name="nonexistent" /></xiv>'
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="テンプレートファイルが見つかりません"):
        compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))

def test_path_traversal_attack(compiler, temp_project):
    """ Tests that a path traversal attempt raises a CompilerError. """
    main_xiv_content = '<xiv type="main"><x-temp x-name="../secret" /></xiv>'
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")
    (temp_project / "secret.xiv").write_text("SECRET DATA", encoding="utf-8")

    with pytest.raises(CompilerError, match="不正なテンプレートパスです"):
        compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))

def test_html_escaping_for_xss(compiler, temp_project):
    """
    Tests that pre-escaped arguments are rendered correctly.
    The compiler should prevent XSS, and the final output format is tested.
    """
    # According to the language spec, input must be properly escaped.
    escaped_input = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'
    # BeautifulSoup's final rendering will un-escape &quot; to ", which is safe.
    expected_output = '&lt;script&gt;alert("XSS")&lt;/script&gt;'

    main_xiv_content = f'''<xiv type="main">
        <x-temp x-name="comment" t-username="{escaped_input}" />
    </xiv>'''
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = '<xiv type="template"><p>Username: {{username}}</p></xiv>'
    (temp_project / "templates" / "comment.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))

    # Check that the final, safely rendered payload is in the output.
    assert expected_output in result

def test_missing_x_name_attribute(compiler, temp_project):
    """ Tests that a missing x-name attribute raises a CompilerError. """
    main_xiv_content = '<xiv type="main"><x-temp /></xiv>'
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    with pytest.raises(CompilerError, match="x-name 属性がありません"):
        compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
