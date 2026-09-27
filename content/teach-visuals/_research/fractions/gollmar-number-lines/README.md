# Number Line Generator

## Required Environment Variables

`FLASK_SECRET_KEY` - Required for CSRF protection

## Feature Flags

Set environment variable `NUMBER_LINE_FEATURES` to a comma-delimited list including the features you wish to enable. Possible features include:

* `np` - Enable number path feature
* `png_preview` - Show PNG at top of page, instead of SVG
