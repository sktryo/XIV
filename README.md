[![test](https://github.com/sktryo/XIV/actions/workflows/test.yml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/test.yml)
[![Publish to NPM](https://github.com/sktryo/XIV/actions/workflows/publish_npm.yaml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/publish_npm.yaml)
# XIV

A simple, component-based template engine that evolves into a lightweight JavaScript framework.

XIV allows you to write clean, reusable HTML components and bring them to life with minimal JavaScript, powered by a Python-based compiler.

## Features

- **Component-Based Architecture:** Use `<x-temp>` to build your UI from reusable parts.
- **Props:** Pass data to components with `t-*` attributes.
- **Slots:** Inject complex HTML content into your components.
- **Conditional Rendering:** Use `x-if` and `x-if="not ..."` to show or hide elements.
- **List Rendering:** Loop over arrays violência `x-for="item in items"`.
- **Reactive State:** Manage component state with `x-data`.
- **Event Handling:** Listen to DOM events with `x-on:<event>`.
- **Reactive Text:** Bind state properties to text content with `x-text`.

## Installation

XIV uses a Python-based compiler wrapped in a Node.js CLI. Installation is a two-step process.

### Step 1: Python Environment Setup

First, ensure you have Python 3 and `pip` installed. Then, set up the compiler's dependencies:

```shell
# Clone the repository (or download the source)
git clone https://github.com/sktryo/XIV.git
cd XIV

# Create a virtual environment (recommended)
python3 -m venv venv

# Install required Python packages
venv/bin/pip install -r requirements.txt
```

### Step 2: Install from npm

Once the Python environment is ready, you can install the `xiv-lang` command-line tool globally from npm:

```shell
npm install -g .
# (In a real scenario, this would be: npm install -g xiv-lang)
```

## Usage

Use the `xiv` command to compile your `.xiv` files into a single HTML file.

```shell
xiv <input_file> [options]
```

**Example:**

```shell
xiv docs/main.xiv -o dist/index.html -t docs/templates
```

**Options:**

- `-t, --templates_dir <path>`: Directory for template files (default: `./templates`)
- `-o, --output_file <path>`: Path for the output HTML file (default: `./index.html`)

## Syntax Guide

### Components & Props

```html
<!-- main.xiv -->
<x-temp x-name="greeting" t-message="Hello World" />

<!-- templates/greeting.xiv -->
<xiv type="template">
    <p>{{ message }}</p>
</xiv>
```

### Slots

```html
<!-- main.xiv -->
<x-temp x-name="card">
    <h4>Card Title</h4>
</x-temp>

<!-- templates/card.xiv -->
<xiv type="template">
    <div class="card">
        <slot />
    </div>
</xiv>
```

### Conditional & List Rendering

```html
<div t-users='[{"name": "Alice", "active": true}, {"name": "Bob", "active": false}]'>
    <template x-for="user in users">
        <div x-if="user.active">
            <p>{{ user.name }} is active.</p>
        </div>
    </template>
</div>
```

### Interactive Components

XIV injects a lightweight JavaScript runtime to handle client-side interactivity.

```html
<div x-data='{ "count": 0 }'>
    <p>Count: <span x-text="count"></span></p>
    <button x-on:click="count++">Increment</button>
</div>
```

## License

This project is licensed under the ISC License. See the [LICENSE](./LICENSE) file for details.
