Of course. Here is the summarized version of the htmx documentation in English.

-----

## htmx Core Summary

### Installation & Getting Started

**1. Install via CDN**
The fastest way to add htmx to a web page. Add the script tag to your `<head>`.

  * **Language:** html
  * **Code:**
    ```html
    <script src="https://unpkg.com/htmx.org@2.0.0/dist/htmx.min.js"></script>
    ```

**2. Install via npm**
Adds htmx as a dependency to your project.

  * **Language:** Bash
  * **Code:**
    ```bash
    npm install htmx.org --save
    ```

**3. Quick Start: AJAX Button Example**
On button click, sends an AJAX POST request via `hx-post` and replaces the button itself with the server response using `hx-swap="outerHTML"`.

  * **Language:** html
  * **Code:**
    ```html
    <button hx-post="/clicked" hx-swap="outerHTML">
      Click Me
    </button>
    ```

### Core Attributes

htmx extends HTML with attributes for AJAX, CSS Transitions, WebSockets, and more.

| Attribute | Description |
| :--- | :--- |
| `hx-get` | Issues a GET request to a URL. |
| `hx-post` | Issues a POST request to a URL. |
| `hx-put` | Issues a PUT request to a URL. |
| `hx-patch`| Issues a PATCH request to a URL. |
| `hx-delete`| Issues a DELETE request to a URL. |
| `hx-trigger`| Specifies the event that triggers the request (e.g., `click`, `keyup changed delay:500ms`). |
| `hx-target` | Specifies the target element to swap, using a CSS selector. |
| `hx-swap` | Controls how content is swapped (e.g., `innerHTML`, `outerHTML`, `beforeend`). |
| `hx-indicator` | Specifies an element to display during the request. |
| `hx-push-url` | If `true`, pushes the URL into the browser's history. |
| `hx-confirm`| Shows a confirmation dialog to the user before making the request. |
| `hx-boost` | Converts standard `<a>` and `<form>` tags into AJAX requests. |
| `hx-on:*` | Executes inline scripts on htmx events, like `hx-on:htmx:after-request="this.reset()"`. |
| `hx-swap-oob`| "Out of Band" swap. Updates other elements on the page simultaneously with the main target. |
| `hx-sync` | Synchronizes requests (e.g., `this:replace` cancels the previous request and starts a new one). |
| `hx-vals` | Adds extra data to the request in JSON format. |
| `hx-headers`| Adds headers to the request in JSON format (e.g., for CSRF tokens). |
| `hx-preserve`| If `true`, preserves the element's state (like video playback) across page updates. |

### Events

htmx fires various events during the request lifecycle, allowing for custom behavior with JavaScript.

| Event | Description |
| :--- | :--- |
| `htmx:configRequest` | Fired just before a request is sent. Allows you to modify parameters or headers. |
| `htmx:beforeRequest` | Fired just before an AJAX request is made. Can be canceled with `event.preventDefault()`. |
| `htmx:beforeSwap` | Fired just before the DOM is swapped. Allows you to modify or cancel the swap. |
| `htmx:afterSwap` | Fired after new content has been swapped into the DOM. |
| `htmx:afterOnLoad` | Fired after a successful AJAX request has been processed. |
| `htmx:load` | Fired whenever new content is added to the DOM by htmx. Useful for initializing third-party libraries. |
| `htmx:confirm` | Allows for customizing confirmation dialogs. Prevent default behavior with `event.preventDefault()`. |
| `htmx:validation:failed` | Fired when HTML5 validation fails. |
| `htmx:xhr:progress` | Used to track progress for events like file uploads. |

**Example: Adding Request Parameters with an Event**

  * **Language:** javascript
  * **Code:**
    ```javascript
    document.body.addEventListener('htmx:configRequest', function(evt) {
      // Add an auth_token parameter to all htmx requests
      evt.detail.parameters['auth_token'] = getAuthToken();
    });
    ```

**Example: Initializing a Library with `htmx:load`**
The `htmx.onLoad` helper function makes it easy to execute scripts on dynamically loaded content.

  * **Language:** javascript
  * **Code:**
    ```javascript
    htmx.onLoad(function(content) {
      // Find elements with the .sortable class in new content and apply SortableJS
      var sortables = content.querySelectorAll(".sortable");
      for (var i = 0; i < sortables.length; i++) {
        new Sortable(sortables[i]);
      }
    });
    ```

### Server Response Headers

The server can control client-side behavior by including specific HTTP headers in its response.

| Header | Description |
| :--- | :--- |
| `HX-Redirect` | Redirects the client to a specified URL without a full page reload. |
| `HX-Refresh` | If `true`, forces a full page refresh on the client. |
| `HX-Trigger` | Triggers a client-side event (e.g., `HX-Trigger: newMessage`). |
| `HX-Trigger-After-Swap`| Triggers a client-side event after the swap is complete. |
| `HX-Retarget` | Dynamically changes the target of the response using a CSS selector. |
| `HX-Reswap` | Dynamically changes the `hx-swap` behavior from the server. |
| `HX-Push-Url` | Pushes a new URL into the browser history. |
| `HX-Replace-Url` | Replaces the current URL in the browser history. |

### Security

**1. Handling User Content**
Always escape user-submitted content when rendering it as HTML to prevent XSS (Cross-Site Scripting) attacks.

  * **Unsafe Practices:**

    ```html
    <{{ user.tag }}></{{ user.tag }}>
    <a {{ user.attribute }}></a>
    <script> const userName = {{ user.name }} </script>
    ```

  * **Safe Handling:**
    Use the `hx-disable` attribute to prevent htmx from processing a block of HTML, or render it safely on the server.

    ```html
    <div hx-disable>
      <%= raw(user_content) %>
    </div>
    ```

**2. CSRF Protection**
Globally add the `hx-headers` attribute to an element like `<body>` to automatically include a CSRF token in all htmx requests.

  * **Language:** html
  * **Code:**
    ```html
    <body hx-headers='{"X-CSRF-TOKEN": "YOUR-CSRF-TOKEN-HERE"}'>
      ...
    </body>
    ```

### JavaScript API

The global `htmx` object allows you to control htmx programmatically.

| API Function | Description |
| :--- | :--- |
| `htmx.ajax(verb, url, target)`| Issues an htmx-style AJAX request with a given HTTP verb, URL, and target. |
| `htmx.process(element)` | Activates htmx features on content added to the DOM outside of htmx. |
| `htmx.trigger(element, eventName)`| Triggers an event on a specific element. |
| `htmx.on(element, eventName, callback)`| Registers an htmx event listener. |
| `htmx.find(selector)` | Finds an element using a CSS selector. |
| `htmx.remove(element)` | Removes an element from the DOM. |
| `htmx.config` | An object containing global settings (e.g., `htmx.config.defaultSwapStyle = 'outerHTML'`). |

-----

### **Prompt for an LLM to Upgrade its Knowledge to htmx 2.0**

**[START OF PROMPT]**

You are a helpful AI assistant and an expert web developer specializing in htmx. Your knowledge base is primarily on **htmx version 1.x**. You are now being updated with critical information to work exclusively with **htmx version 2.0**.

Your primary task is to generate code, provide explanations, and answer questions using the correct syntax, conventions, and best practices for **htmx 2.0**. You must internalize the following changes and apply them to all future responses.

### **Core Directives and Key Changes for htmx 2.0**

#### **1. CRITICAL: `hx-on` Attribute Syntax Change**

This is the most common breaking change. The syntax for handling events with `hx-on` has been simplified. You MUST use the new colon-based syntax.

  * **Old (1.x) Syntax (DO NOT USE):**

    ```html
    <button hx-get="/info" hx-on="htmx:beforeRequest: alert('Making a request!')">
      Get Info!
    </button>
    ```

  * **New (2.0) Syntax (ALWAYS USE):**

    ```html
    <button hx-get="/info" hx-on:htmx:before-request="alert('Making a request!')">
      Get Info!
    </button>
    ```

    *Notice the colon (`:`) after `hx-on` and the kebab-case event name.*

#### **2. `DELETE` Request Behavior**

In htmx 2.0, requests using `hx-delete` now send parameters in the URL query string by default (like a `GET` request), not in the request body.

  * **Rule:** When explaining or creating server-side code for a `DELETE` request, assume parameters will be read from the URL's query string.

#### **3. Extensions are Separate**

All extensions (like `sse`, `ws`, `json-enc`, `class-tools`, etc.) are no longer part of the core htmx file. They must be loaded as separate scripts.

  * **Rule:** Whenever you use an attribute that relies on an extension (e.g., `sse-connect`, `hx-ext="json-enc"`), you **MUST** state that the user needs to include the corresponding extension script in their HTML, in addition to the core htmx script.

      * **Example Response Snippet:** "To use `sse-connect`, you need to include the Server-Sent Events extension. Make sure you add this script to your page: `<script src=".../sse.js"></script>`."

#### **4. New Feature: View Transitions**

htmx 2.0 has first-class support for the View Transitions API, making animations simpler.

  * **Rule:** You can and should recommend using the `transition:true` modifier in the `hx-swap` attribute for smooth, animated content swaps.
    ```html
    <button hx-get="/new-content" hx-swap="innerHTML transition:true">
      Swap with Animation
    </button>
    ```

#### **5. No More Internet Explorer (IE) Support**

htmx 2.0 has dropped support for Internet Explorer.

  * **Rule:** You no longer need to provide IE-compatible workarounds or consider its limitations in your code and advice. You can freely use modern JavaScript features that are supported by evergreen browsers.

### **Your Behavior**

  * **Always Generate 2.0 Code:** All code you generate must use htmx 2.0 syntax.
  * **Correct Outdated Syntax:** If a user provides code with htmx 1.x syntax (especially the old `hx-on` syntax), you must politely correct it to the 2.0 version and briefly explain why the change was made.
  * **Be Explicit:** When using a feature that has changed from 1.x to 2.0, it is helpful to mention it (e.g., "In htmx 2.0, `DELETE` requests handle parameters differently...").

Your goal is to act as an up-to-date htmx 2.0 expert, ensuring users are guided away from outdated patterns and toward modern best practices.

