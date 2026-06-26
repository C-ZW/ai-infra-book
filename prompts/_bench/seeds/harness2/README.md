# text-transform plugins

Build a plugin system for text transforms.

Requirements:
- a registry where plugins register by name, e.g. a `@register('upper')` decorator
- `run_pipeline(text, ['upper', 'reverse'])` applies registered plugins by name, in order
- ship two example plugins: `upper` (uppercase) and `reverse` (reverse the string)
- a test
- **Adding a new plugin must not require editing the core registry/runner.**
