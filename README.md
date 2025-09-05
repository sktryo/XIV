[![Test Status](https://github.com/sktryo/XIV/actions/workflows/test.yml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/test.yml)
[![Compile Docs](https://github.com/sktryo/XIV/actions/workflows/compile-docs.yml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/compile-docs.yml)
[![Publish to Bun](https://github.com/sktryo/XIV/actions/workflows/publish.yml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/publish.yml)

# XIV

A simple, component-based template engine that evolves into a lightweight JavaScript framework.

XIV allows you to write clean, reusable HTML components and bring them to life with minimal JavaScript, all powered by the Bun runtime.

## Features

XIV provides a powerful set of directives to make your HTML dynamic and interactive.

- **`x-data`**: Initializes a component's state as a JavaScript object.
  ```html
  <div x-data="{ count: 0, message: 'Hello' }">...</div>
  ```

- **`x-init`**: Runs an expression when a component is initialized.
  ```html
  <div x-data="{ users: [] }" x-init="users = await (await fetch('/api/users')).json()">...</div>
  ```

- **`x-text`**: Binds the text content of an element to a state property.
  ```html
  <span x-text="message"></span>
  ```

- **`x-on:<event>`**: Attaches an event listener to an element.
  ```html
  <button x-on:click="count++">Increment</button>
  ```

- **`x-bind:<attribute>`**: Binds an element's attribute to a state property.
  ```html
  <a x-bind:href="url">Visit Site</a>
  ```

- **`x-model`**: Creates a two-way data binding on an input element.
  ```html
  <input type="text" x-model="message">
  ```

- **`x-if`**: Conditionally renders an element based on an expression.
  ```html
  <template x-if="isOpen">
    <div>Now you see me.</div>
  </template>
  ```

- **`x-for`**: Renders a list of elements from an array.
  ```html
  <template x-for="user in users">
    <div x-text="user.name"></div>
  </template>
  ```

- **`x-ref`**: Provides a way to directly access a DOM element within your component.
  ```html
  <input type="text" x-ref="myInput">
  <button x-on:click="$refs.myInput.focus()">Focus Input</button>
  ```

## Installation

First, ensure you have [Bun](https://bun.sh/) installed.

```shell
# Install from the Bun package registry
bun add xiv-lang
```

## Usage

### Compiling with the CLI

Use the `xiv` command to compile your `.xiv` files into a single HTML file.

```shell
xiv <input_file> [options]
```

**Example:**

```shell
xiv docs/main.xiv -o dist/index.html
```

**Options:**

- `-o, --output_file <path>`: Path for the output HTML file (default: `./index.html`)

### Creating Reusable Components

You can create reusable components and load them into your main file using the `<x-temp>` element.

**`templates/my-card.xiv`:**
```html
<div class="card">
    <h2 x-text="user.name"></h2>
    <p><a x-bind:href="`mailto:${user.email}`" x-text="user.email"></a></p>
    <p><strong>Website:</strong> <a x-bind:href="`http://${user.website}`" target="_blank" x-text="user.website"></a></p>
</div>
```

**`main.xiv`:**
```html
<xiv type="main">
    <body>
        <div x-data="{ users: [] }" x-init="/* fetch users from an API */">
            <h1>User Directory</h1>
            <div class="grid">
                <template x-for="user in users">
                    <!-- Pass the 'user' object to the component's scope -->
                    <div x-data="{ user: user }">
                         <x-temp src="templates/my-card.xiv"></x-temp>
                    </div>
                </template>
            </div>
        </div>
    </body>
</xiv>
```

## Development

To contribute or run the project locally:

```shell
# Clone the repository
git clone https://github.com/sktryo/XIV.git
cd XIV

# Install dependencies
bun install

# Build the runtime (after making changes in src/runtime/)
bun run build:runtime

# Run tests
bun test
```

## How It Works

The `xiv` compiler takes a main `.xiv` file, extracts the content from `<head>` and `<body>` tags inside a `<xiv type="main">` block, and embeds it into a standard HTML5 boilerplate. It also includes the `xiv.js` runtime via a `<script>` tag, which powers all the client-side interactive features.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
