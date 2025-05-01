# 🕒 Age Timer with Space Travel

![Age Timer](https://raw.githubusercontent.com/pkeffect/open-webui-tools/main/age_travel/icon.png)

A fascinating Open WebUI extension that calculates not only how long you've been alive but also how far you've traveled through the cosmos during your lifetime!

## 🌟 Overview

Age Timer with Space Travel is a unique tool that answers two intriguing questions:
1. **How long have you been alive?** - Down to the minute with precise leap year handling
2. **How far have you traveled through space?** - Based on Earth's movements through the cosmos

The calculations consider Earth's orbit around the Sun (107,226 km/h) and our solar system's movement through the Milky Way galaxy (720,000 km/h), resulting in mind-boggling distances that will give you a new perspective on your cosmic journey!

## ✨ Features

- 🧮 **Precise Age Calculation** - Years, months, days, hours, and minutes since birth with accurate leap year handling
- 🚀 **Space Travel Distance** - Computes how far you've traveled through the cosmos based on:
  - Earth's orbit around the Sun (107,226 km/h)
  - Solar system's movement through the Milky Way galaxy (720,000 km/h)
- 🌍 **Complete Timezone Support** - Select from all global timezones with a convenient dropdown
- ☀️ **Daylight Saving Time Handling** - Toggle DST support for accurate calculations across time changes
- 📅 **Custom Date Option** - Calculate hypothetical ages like "How old will I be on date X?"
- 📊 **Smart Distance Formatting** - Displays astronomical distances intelligently (light years, billions of km, etc.)
- 🔄 **Real-time Updates** - Shows calculation progress with detailed status messages

## ⚙️ Configuration Options

| Setting | Description | Default Value |
|---------|-------------|---------------|
| `birth_date` | Your birth date (YYYY-MM-DD HH:MM) | None (required input) |
| `use_custom_current_date` | Override the current date with a custom value | `False` |
| `custom_current_date` | Custom current date for hypothetical age calculations | None |
| `timezone` | Select your timezone from a dropdown of all global options | `UTC` |
| `account_for_dst` | Whether to account for Daylight Saving Time transitions | `True` |
| `AUTO_CLOSE_OUTPUT` | Automatically close/collapse output when finished | `True` |
| `AUTO_CLOSE_DELAY` | Seconds to wait before auto-closing output | `60` |

## 📦 Installation

1. In Open WebUI, navigate to the Extensions panel
2. Find "Age Timer with Space Travel" in the community extensions
3. Click "Install"
4. The tool will now appear in your toolbar for easy access

## 🚀 Usage

1. Click the Age Timer with Space Travel button in Open WebUI
2. Enter your birth date in the format YYYY-MM-DD HH:MM (e.g., 1990-05-15 10:30)
3. Configure your preferences:
   - Select your timezone from the dropdown
   - Toggle DST handling
   - Optionally enable custom current date
4. Click "Run" to calculate your age and space travel distance
5. Marvel at how far you've traveled through the cosmos!

## 📊 Sample Output

```
✨ Time Alive! ✨ 🎂 Years: 35, Months: 0 (approximate), Days: 2, Hours: 4, Minutes: 0 | Space Travel: 2.87 light years
```

## 🧮 How It Works

### Age Calculation
The tool calculates your exact age by:
1. Computing the difference between your birth date and the current date
2. Accounting for leap years and complex timezone differences
3. Breaking down the result into years, months, days, hours, and minutes

### Space Travel Distance
Your cosmic travel distance is calculated based on:
1. **Earth's orbit around the Sun**: ~107,226 km/h
2. **Solar system's movement through the galaxy**: ~720,000 km/h
3. Your total lifetime in hours
4. The result is formatted in appropriate units (light years, billions of km, etc.)

## ⚠️ Important Notes

- Month calculations are approximate due to varying month lengths
- Space travel distances are fascinating but approximate
- Timezone calculations properly account for DST transitions when enabled
- Custom current date option allows for hypothetical "how old would I be on date X" calculations
- All calculations properly handle timezone differences between birth date and current date

## 📝 Changelog

- **0.0.9** - Major update with timezone dropdown selection, DST toggle, and custom date option
- **0.0.8** - Added support for all global timezones with proper timezone handling
- **0.0.7** - Enhanced daylight savings time support with toggle option
- **0.0.6** - Added ability to override current date/time with custom values
- **0.0.5** - Added space travel calculations showing distance traveled through the cosmos
- **0.0.4** - Improved leap year handling and timezone detection
- **0.0.3** - Added automatic current time detection
- **0.0.2** - Enhanced status reporting and user interface
- **0.0.1** - Initial release with basic age calculation

## 👨‍💻 Author

Developed by [pkeffect](https://github.com/pkeffect/)

## 🔗 Links

- [Project Repository](https://github.com/pkeffect/open-webui-tools/tree/main/age_travel)
- [Open WebUI](https://github.com/open-webui)

## 📄 License

This project is licensed under the MIT License

---

**Required Open WebUI Version:** 0.6.0 or higher
