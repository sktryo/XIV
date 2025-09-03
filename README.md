[![test](https://github.com/sktryo/XIV/actions/workflows/test.yml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/test.yml)
[![Publish to Bun](https://github.com/sktryo/XIV/actions/workflows/publish.yml/badge.svg)](https://github.com/sktryo/XIV/actions/workflows/publish.yml)

# XIV

A simple, component-based template engine that evolves into a lightweight JavaScript framework.

XIV allows you to write clean, reusable HTML components and bring them to life with minimal JavaScript, all powered by the Bun runtime.

## Features

The compiler sets up a basic HTML structure, while the lightweight JavaScript runtime handles dynamic features directly in the browser.

- **Component-Based Architecture:** Build your UI from reusable parts.
- **Props:** Pass data to components.
- **Slots:** Inject complex HTML content into your components.
- **Conditional Rendering:** Use `x-if` to show or hide elements.
- **List Rendering:** Loop over arrays with `x-for`.
- **Reactive State:** Manage component state with `x-data`.
- **Event Handling:** Listen to DOM events with `x-on:<event>`.
- **Reactive Text:** Bind state properties to text content with `x-text`.

## Installation

First, ensure you have [Bun](https://bun.sh/) installed.

```shell
# Install from the Bun package registry
bun add xiv-lang
```

## Usage

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

## Development

To contribute or run the project locally:

```shell
# Clone the repository
git clone https://github.com/sktryo/XIV.git
cd XIV

# Install dependencies
bun install

# Run tests
bun test
```

## How It Works

The `xiv` compiler takes a main `.xiv` file, extracts the content from `<head>` and `<body>` tags inside a `<xiv type="main">` block, and embeds it into a standard HTML5 boilerplate. It also injects the `xiv.js` runtime, which powers all the client-side interactive features.

**Example `main.xiv`:**
```html
<xiv type="main">
    <head>
        <title>My Awesome App</title>
    </head>
    <body>
        <h1>Welcome to XIV!</h1>

        <!-- Interactive component handled by the runtime -->
        <div x-data='{ "count": 0 }'>
            <p>Count: <span x-text="count"></span></p>
            <button x-on:click="count++">Increment</button>
        </div>
    </body>
</xiv>
```

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.