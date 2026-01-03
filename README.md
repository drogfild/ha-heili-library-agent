# ha-heili-library-agent

Home Assistant AppDaemon agent that automates Heili library accounts.
The agent logs into the Heili library system using headless Selenium, fetches loan due dates, renews all loans on demand, and synchronizes the data into Home Assistant entities.

## Features

The agent supports multiple library accounts and runs fully headless using Selenium.
It fetches loan due dates and stores them in input_datetime entities.
Loans can be renewed on demand using input_boolean triggers.
Due dates are refreshed automatically once per day.
Execution is staggered to avoid excessive load on the library service.
The project is designed specifically for Home Assistant and AppDaemon.

This project is intended as a home automation agent, not a general-purpose web scraping library.

## Requirements

Home Assistant  
AppDaemon  
Chrome or Chromium available on the host  
Compatible ChromeDriver  
Network access to https://heilikirjastot.fi

## Installation

Copy the Python file into your AppDaemon apps directory.

apps/
  heili_library_agent.py

Restart AppDaemon after copying the file.

Create the required Home Assistant helpers:
One input_datetime per account to store the due date.
One input_boolean per account to trigger loan renewal.

## AppDaemon Add-on configuration (Home Assistant)

When running AppDaemon as a Home Assistant Add-on, additional packages must be configured explicitly.

Open the AppDaemon add-on configuration page and add the following:

System packages:
- chromium-chromedriver

Python packages:
- selenium

These settings ensure that:
- A compatible ChromeDriver binary is available in the container
- Selenium is installed and usable by the agent

After changing these settings, restart the AppDaemon add-on.

Without these packages, the agent will fail to start the headless browser.


## Example Home Assistant helpers

Example input_datetime:

input_datetime:
  webscrape_heili_date_example:
    name: Heili Due Date (Example)
    has_date: true
    has_time: false

Example input_boolean:

input_boolean:
  run_webscrape_heili_renew_all_example:
    name: Renew Heili Loans (Example)

## AppDaemon configuration

Example apps.yaml configuration using generic account names:

HeiliLibraryAgent:
  module: HeiliLibraryAgent
  class: HeiliLibraryAgent

  account_names:
    - account1
    - account2

  heili_account1_username: !secret heili_account1_username
  heili_account1_password: !secret heili_account1_password

  heili_account2_username: !secret heili_account2_username
  heili_account2_password: !secret heili_account2_password

  update_time: "03:00:00"

The update_time setting is optional.
If not specified, the agent defaults to running daily updates at 03:00.

## Account mapping logic

For each account name listed in account_names, the agent expects the following.

Secrets:
heili_<account>_username
heili_<account>_password

Home Assistant entities:
input_boolean.run_webscrape_heili_renew_all_<account>
input_datetime.webscrape_heili_date_<account>

The <account> value must match exactly between account_names, secrets, and entity IDs.

## How it works

On startup, the agent fetches due dates for all configured accounts.
Once per day, it refreshes all due dates at the configured time.
When an account-specific input_boolean is turned on, the agent logs in, renews all loans, fetches the new due date, updates the corresponding input_datetime entity, and turns the input_boolean off automatically.

All browser sessions are executed headlessly and isolated per operation.

## Security notes

Credentials must be stored using Home Assistant secrets.
No credentials are logged.
This project interacts with a third-party service.
You are responsible for ensuring that your use complies with the service’s terms of use.

## Limitations

The agent relies on the current DOM structure of the Heili library website.
Changes to the UI or login flow may break functionality.
There is no CAPTCHA handling.
Retry and backoff logic is minimal.

## License

MIT License
