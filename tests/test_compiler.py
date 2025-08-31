import os
import re
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

def test_default_value_in_template(compiler, temp_project):
    """ Tests that default values are used when arguments are not provided. """
    main_xiv_content = """<xiv type="main">
    <x-temp x-name="user_profile" t-name="Alice" />
    <x-temp x-name="user_profile" />
</xiv>"""
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = '<xiv type="template"><p>Name: {{name|Guest}}, Age: {{age|30}}</p></xiv>'
    (temp_project / "templates" / "user_profile.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')
    
    profiles = soup.find_all('div', class_='x-user_profile')
    assert len(profiles) == 2
    
    # First profile with provided name
    assert "Name: Alice" in profiles[0].p.text
    assert "Age: 30" in profiles[0].p.text # Default age
    
    # Second profile with all defaults
    assert "Name: Guest" in profiles[1].p.text
    assert "Age: 30" in profiles[1].p.text

def test_nested_templates_with_defaults(compiler, temp_project):
    """ Tests nested templates where the inner template uses a default value. """
    main_xiv_content = '<xiv type="main"><x-temp x-name="outer" t-outer_text="Provided" /></xiv>'
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    outer_template = """<xiv type="template">
    <div class="outer">
        <p>{{outer_text}}</p>
        <x-temp x-name="inner" />
    </div>
</xiv>"""
    (temp_project / "templates" / "outer.xiv").write_text(outer_template, encoding="utf-8")

    inner_template = '<xiv type="template"><span class="inner">{{inner_text|Default Inner}}</span></xiv>'
    (temp_project / "templates" / "inner.xiv").write_text(inner_template, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    outer_div = soup.find('div', class_='x-outer')
    assert outer_div is not None
    assert "Provided" in outer_div.p.text
    
    inner_span = outer_div.find('span', class_='inner')
    assert inner_span is not None
    assert "Default Inner" in inner_span.text

def test_slot_functionality(compiler, temp_project):
    """Tests that content inside a component tag (slot) is rendered correctly."""
    main_xiv_content = """<xiv type="main">
    <x-temp x-name="wrapper">
        <p>This is the slot content.</p>
        <x-temp x-name="inner" t-text="Inner component" />
    </x-temp>
</xiv>"""
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    wrapper_template = """<xiv type="template">
    <div class="wrapper">
        <h1>Wrapper Title</h1>
        <div class="content">
            <x-slot />
        </div>
    </div>
</xiv>"""
    (temp_project / "templates" / "wrapper.xiv").write_text(wrapper_template, encoding="utf-8")

    inner_template = '<xiv type="template"><span>{{text}}</span></xiv>'
    (temp_project / "templates" / "inner.xiv").write_text(inner_template, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    wrapper_div = soup.find('div', class_='x-wrapper')
    assert wrapper_div is not None
    assert wrapper_div.find('h1').text.strip() == "Wrapper Title"
    
    content_div = wrapper_div.find('div', class_='content')
    assert content_div is not None
    assert content_div.find('p').text.strip() == "This is the slot content."

    inner_component = content_div.find('div', class_='x-inner')
    assert inner_component is not None
    assert inner_component.find('span').text.strip() == "Inner component"

def test_empty_slot(compiler, temp_project):
    """Tests that an empty slot is handled correctly."""
    main_xiv_content = '<xiv type="main"><x-temp x-name="wrapper"></x-temp></xiv>'
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    wrapper_template = '<xiv type="template"><div><x-slot /></div></xiv>'
    (temp_project / "templates" / "wrapper.xiv").write_text(wrapper_template, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    wrapper_div = soup.find('div', class_='x-wrapper')
    assert wrapper_div is not None
    # The inner div should be empty
    assert wrapper_div.find('div').text.strip() == ""
    inner_div_contents = wrapper_div.find('div').contents
    assert not inner_div_contents or all(isinstance(c, str) and c.strip() == '' for c in inner_div_contents)

def test_x_if_directive_true(compiler, temp_project):
    """Tests that x-if directive keeps element when condition is true."""
    main_xiv_content = """<xiv type="main">
    <x-temp x-name="conditional" t-show="true" />
</xiv>"""
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = """<xiv type="template">
    <div x-if="show">This should be visible.</div>
    <p x-if="not show">This should be hidden.</p>
</xiv>"""
    (temp_project / "templates" / "conditional.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')
    
    assert "This should be visible." in soup.text
    assert "This should be hidden." not in soup.text
    assert soup.find('div', string=re.compile(r"\s*This should be visible.\s*")) is not None
    assert soup.find('p', string=re.compile(r"\s*This should be hidden.\s*")) is None

def test_x_if_directive_false(compiler, temp_project):
    """Tests that x-if directive removes element when condition is false."""
    main_xiv_content = """<xiv type="main">
    <x-temp x-name="conditional" t-show="false" />
</xiv>"""
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = """<xiv type="template">
    <div x-if="show">This should be hidden.</div>
    <p x-if="not show">This should be visible.</p>
</xiv>"""
    (temp_project / "templates" / "conditional.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    assert "This should be hidden." not in soup.text
    assert "This should be visible." in soup.text
    assert soup.find('div', string=re.compile(r"\s*This should be hidden.\s*")) is None
    assert soup.find('p', string=re.compile(r"\s*This should be visible.\s*")) is not None

def test_x_if_directive_undefined(compiler, temp_project):
    """Tests that x-if directive removes element when variable is undefined."""
    main_xiv_content = """<xiv type="main">
    <x-temp x-name="conditional" />
</xiv>"""
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = """<xiv type="template">
    <div x-if="show">This should be hidden.</div>
    <p x-if="not show">This should be visible.</p>
</xiv>"""
    (temp_project / "templates" / "conditional.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    assert "This should be hidden." not in soup.text
    assert "This should be visible." in soup.text
    assert soup.find('div', string=re.compile(r"\s*This should be hidden.\s*")) is None
    assert soup.find('p', string=re.compile(r"\s*This should be visible.\s*")) is not None

def test_x_for_simple_list(compiler, temp_project):
    """Tests x-for with a simple list of strings."""
    main_xiv_content = '''<xiv type="main">
    <x-temp x-name="looper" t-items='["Apple", "Banana", "Cherry"]' />
</xiv>'''
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = '''<xiv type="template">
    <ul>
        <li x-for="item in items">{{ item }}</li>
    </ul>
</xiv>'''
    (temp_project / "templates" / "looper.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    list_items = soup.find_all('li')
    assert len(list_items) == 3
    assert list_items[0].text.strip() == "Apple"
    assert list_items[1].text.strip() == "Banana"
    assert list_items[2].text.strip() == "Cherry"

def test_x_for_object_list(compiler, temp_project):
    """Tests x-for with a list of objects and nested property access."""
    import json
    user_list = [
        {"name": "Alice", "age": 30, "isActive": True},
        {"name": "Bob", "age": 25, "isActive": False}
    ]
    user_data_json = json.dumps(user_list)

    main_xiv_content = f'''<xiv type="main">
    <x-temp x-name="user-list" t-users='{user_data_json}' />
</xiv>'''
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = '''<xiv type="template">
    <div x-for="user in users">
        <p class="name">{{ user.name }}</p>
        <p class="age">Age: {{ user.age }}</p>
        <p class="status" x-if="user.isActive">Status: Active</p>
    </div>
</xiv>'''
    (temp_project / "templates" / "user-list.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    users = soup.find('div', class_='x-user-list').find_all('div', recursive=False)
    assert len(users) == 2
    
    assert users[0].find('p', class_='name').text.strip() == "Alice"
    assert users[0].find('p', class_='age').text.strip() == "Age: 30"
    assert users[0].find('p', class_='status') is not None

    assert users[1].find('p', class_='name').text.strip() == "Bob"
    assert users[1].find('p', class_='age').text.strip() == "Age: 25"
    assert users[1].find('p', class_='status') is None

def test_x_for_empty_list(compiler, temp_project):
    """Tests that x-for renders nothing for an empty list."""
    main_xiv_content = '''<xiv type="main">
    <x-temp x-name="looper" t-items='[]' />
</xiv>'''
    (temp_project / "main.xiv").write_text(main_xiv_content, encoding="utf-8")

    template_content = '''<xiv type="template">
    <p>Header</p>
    <div x-for="item in items">{{ item }}</div>
    <p>Footer</p>
</xiv>'''
    (temp_project / "templates" / "looper.xiv").write_text(template_content, encoding="utf-8")

    result = compiler.compile(str(temp_project / "main.xiv"), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    # The div with x-for should not be rendered
    assert len(soup.find('div', class_='x-looper').find_all('div')) == 0
    assert "Header" in soup.text
    assert "Footer" in soup.text

def test_runtime_injection(compiler, temp_project):
    """Tests that the xiv.js runtime is correctly injected into the final HTML."""
    main_xiv_content = """<xiv type="main">
    <body>
        <div x-data="{ count: 0 }"></div>
    </body>
</xiv>"""
    main_xiv_file = temp_project / "main.xiv"
    main_xiv_file.write_text(main_xiv_content, encoding="utf-8")

    result = compiler.compile(str(main_xiv_file), str(temp_project / "templates"))
    soup = BeautifulSoup(result, 'lxml')

    script_tag = soup.find('script')
    assert script_tag is not None
    
    # Check for a specific, unique string from the actual runtime file
    assert "const XIV = {" in script_tag.string
    assert "document.addEventListener('DOMContentLoaded'" in script_tag.string
