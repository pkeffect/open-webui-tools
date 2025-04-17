"""
title: Age Timer with Space Travel
description: How long you been alive and how far you have traveled
author: pkeffect
author_url: https://github.com/pkeffect/
project_url: https://github.com/pkeffect/open-webui-tools/tree/main/age_travel
funding_url: https://github.com/open-webui
required_open_webui_version: 0.6.0
version: 0.0.5
date: 2025-04-17
license: MIT
changelog:
  - 0.0.9 - Major update with timezone dropdown selection, DST toggle, and custom date option
  - 0.0.8 - Added support for all global timezones with proper timezone handling
  - 0.0.7 - Enhanced daylight savings time support with toggle option
  - 0.0.6 - Added ability to override current date/time with custom values
  - 0.0.5 - Added space travel calculations showing distance traveled through the cosmos
  - 0.0.4 - Improved leap year handling and timezone detection
  - 0.0.3 - Added automatic current time detection
  - 0.0.2 - Enhanced status reporting and user interface
  - 0.0.1 - Initial release with basic age calculation
features:
  - Calculates years, months, days, hours, and minutes since birth with precise leap year handling
  - Automatically detects current time with comprehensive timezone support
  - Complete timezone support with dropdown selection featuring all global timezones
  - Customizable daylight savings time handling with toggle control
  - Optional override of current date/time for hypothetical age calculations
  - Computes cosmic travel distance based on Earth's rotation, orbit around the Sun, and solar system's movement through the galaxy
  - Formats astronomical distances intelligently (light years, billions of km, etc.)
  - Shows progress with detailed status updates
  - User-friendly interface with Valves integration
  - Proper display of DST and timezone information in results
important:
  - Calculations include Earth's orbit around Sun (107,226 km/h) and solar system movement through galaxy (720,000 km/h)
  - Month calculations are approximate due to varying month lengths
  - Space travel distances are fascinating but approximate
  - Timezone calculations properly account for DST transitions when enabled
  - Custom current date option allows for hypothetical "how old would I be on date X" calculations
  - All calculations properly handle timezone differences between birth date and current date
requirements:
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, List
import datetime
import asyncio
import time
import threading
import pytz


def calculate_age_components(birth_datetime, current_datetime):
    """Calculates age components (years, months, days, hours, minutes)
    and accounts for leap years.
    """
    # Ensure both datetimes are timezone-aware or both are naive
    if birth_datetime.tzinfo is None and current_datetime.tzinfo is not None:
        birth_datetime = birth_datetime.replace(tzinfo=current_datetime.tzinfo)
    elif birth_datetime.tzinfo is not None and current_datetime.tzinfo is None:
        current_datetime = current_datetime.replace(tzinfo=birth_datetime.tzinfo)

    time_difference = current_datetime - birth_datetime

    years = 0
    months = 0
    days = time_difference.days
    seconds = time_difference.seconds

    # Calculate years with leap year handling
    while True:
        try:
            test_date = birth_datetime.replace(year=birth_datetime.year + years + 1)
            if test_date <= current_datetime:
                years += 1
            else:
                break
        except ValueError:  # Handle Feb 29th on non-leap year
            test_date = birth_datetime.replace(
                year=birth_datetime.year + years + 1, day=28
            )  # Move to Feb 28th
            if test_date <= current_datetime:
                years += 1
            else:
                break

    # Adjust days after calculating years
    age_after_years = birth_datetime.replace(year=birth_datetime.year + years)
    days_after_years = (current_datetime - age_after_years).days
    days = days_after_years

    # Calculate months (approximate) - more accurate month calculation is complex due to varying month lengths
    months = (
        days // 30
    )  # Approximate months, can be refined further if needed for exact month count
    days = (
        days % 30
    )  # Remaining days after approximate month calculation (this is a simplification)

    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60

    return years, months, days, hours, minutes


def calculate_space_travel(years, months, days, hours, minutes):
    """Calculate how far the person has traveled through space during their lifetime.

    Based on Earth's movement through space:
    - Earth's rotation: ~1,670 km/h at equator
    - Earth's orbit around Sun: ~107,226 km/h
    - Solar system's movement around galaxy: ~720,000 km/h

    Returns distance in kilometers
    """
    # Convert all time components to hours for calculation
    total_hours = (
        (years * 365.25 * 24)
        + (months * 30 * 24)
        + (days * 24)
        + hours
        + (minutes / 60)
    )

    # Earth's orbit around the Sun: ~107,226 km/h
    orbit_distance = total_hours * 107226

    # Solar system around galaxy: ~720,000 km/h
    galaxy_distance = total_hours * 720000

    # Total distance traveled through space (orbit + galaxy movement)
    total_distance = orbit_distance + galaxy_distance

    return total_distance


def get_current_datetime(timezone_str=None):
    """Get the current datetime with timezone information

    Args:
        timezone_str: Optional timezone string (e.g., 'America/New_York')
                     If None, use local timezone
    """
    # Get current time in UTC first
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # Convert to specified timezone or local timezone
    if timezone_str:
        try:
            timezone = pytz.timezone(timezone_str)
            return now_utc.astimezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fall back to local timezone if unknown timezone
            return datetime.datetime.now().astimezone()
    else:
        # Use local timezone
        return datetime.datetime.now().astimezone()


def format_distance(distance_km):
    """Format large distances in a readable way"""
    # For very large distances, convert to light years
    light_year_km = 9.461e12

    if distance_km > light_year_km:
        light_years = distance_km / light_year_km
        return f"{light_years:.2f} light years"

    # For large distances but less than a light year, use billions or trillions
    if distance_km > 1e12:  # trillion
        return f"{distance_km/1e12:.2f} trillion km"
    elif distance_km > 1e9:  # billion
        return f"{distance_km/1e9:.2f} billion km"
    elif distance_km > 1e6:  # million
        return f"{distance_km/1e6:.2f} million km"
    else:
        return f"{distance_km:.2f} km"


def get_all_timezones():
    """Returns a sorted list of all available timezones from pytz"""
    return sorted(pytz.all_timezones)


def parse_datetime_with_timezone(datetime_str, timezone_str=None):
    """Parse a datetime string and apply a timezone if specified.

    Args:
        datetime_str: String in format 'YYYY-MM-DD HH:MM'
        timezone_str: Optional timezone string (e.g., 'America/New_York')
                      If None, datetime will be naive

    Returns:
        Datetime object with timezone information if specified
    """
    # Parse the basic datetime without timezone
    dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

    # Apply timezone if specified
    if timezone_str:
        try:
            timezone = pytz.timezone(timezone_str)
            # Localize the datetime (accounting for DST if applicable)
            dt = timezone.localize(dt)
        except (pytz.exceptions.UnknownTimeZoneError, ValueError):
            # If timezone is invalid, return naive datetime
            pass

    return dt


class Action:
    class Valves(BaseModel):
        # Birth date input
        birth_date: Optional[str] = Field(
            None, description="Enter your birth date (YYYY-MM-DD HH:MM)"
        )

        # Added current date override option
        use_custom_current_date: bool = Field(
            default=False,
            description="Override the current date/time with a custom value",
        )
        custom_current_date: Optional[str] = Field(
            None, description="Custom current date (YYYY-MM-DD HH:MM) if overriding"
        )

        # Time zone selection - we'll populate this dynamically in __init__
        timezone: str = Field(default="UTC", description="Select your time zone")

        # Daylight Savings Time handling as boolean toggle
        account_for_dst: bool = Field(
            default=True, description="Account for Daylight Savings Time transitions"
        )

        # Auto-close settings
        AUTO_CLOSE_OUTPUT: bool = Field(
            default=True,
            description="Whether to automatically close/collapse output when finished",
        )
        AUTO_CLOSE_DELAY: int = Field(
            default=60,
            description="Seconds to wait before automatically closing output (default: 60)",
        )

    def __init__(self):
        # Get list of timezones for dropdown
        self.available_timezones = get_all_timezones()

        # Create a custom Valves class with the timezone enum populated
        class ValvesWithTimezones(self.Valves):
            # Dynamically create a new field with the enum populated
            timezone: str = Field(
                default="UTC",
                description="Select your time zone",
                enum=get_all_timezones(),
            )

        # Use the custom Valves class with timezones
        self.valves = ValvesWithTimezones()

        # For tracking output closure
        self.close_task = None
        # For tracking event emitter
        self.event_emitter = None
        # For tracking operations
        self.is_operation_complete = False
        # For thread safety
        self.lock = threading.Lock()

    def create_message(
        self, type_name, description="", status="in_progress", done=False, close=False
    ):
        """Create a unified message structure for the event emitter"""
        message_id = f"msg_{int(time.time() * 1000)}"
        message = {
            "type": type_name,
            "message_id": message_id,
            "data": {
                "status": status,
                "description": description,
                "done": done,
                "close": close,
                "message_id": message_id,
            },
        }
        return message

    async def close_emitter_output(self):
        """Send a final message to close/collapse the output"""
        await asyncio.sleep(self.valves.AUTO_CLOSE_DELAY)

        if self.event_emitter and self.is_operation_complete:
            # Try several different approaches to signal completion:
            # 1. Send a special close message
            close_msg = self.create_message(
                "status", description="", status="complete", done=True, close=True
            )
            await self.event_emitter(close_msg)

            # 2. Send an empty message to signal end of stream (works in some systems)
            await self.event_emitter({})

            # 3. Try a close_output event type (might work in some implementations)
            await self.event_emitter(
                {"type": "close_output", "data": {"force_close": True}}
            )

            # 4. Try to clear all messages
            await self.event_emitter(
                {"type": "clear_all", "data": {"force_clear": True}}
            )

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__: Callable[[dict], Any] = None,
        __event_call__: Callable[[dict], Any] = None,
    ) -> Optional[dict]:
        if not __event_emitter__:
            return

        # Store the event emitter for later use
        self.event_emitter = __event_emitter__
        self.is_operation_complete = False

        try:
            # Initial status message
            initial_message = self.create_message(
                "status",
                "Starting Enhanced Age Timer calculation...",
            )
            await __event_emitter__(initial_message)

            # Use values from the Valves (already filled in from the UI)
            timezone_response = self.valves.timezone
            account_for_dst = self.valves.account_for_dst
            use_custom_date = self.valves.use_custom_current_date
            custom_date = self.valves.custom_current_date if use_custom_date else None

            # Check if birth date is provided
            if not self.valves.birth_date:
                # If birth date is not provided through Valves, ask for it directly
                await __event_emitter__(
                    self.create_message(
                        "status", "Requesting birth date information..."
                    )
                )
                birth_date_response = await __event_call__(
                    {
                        "type": "input",
                        "data": {
                            "title": "Birth Date",
                            "message": "Enter your birth date (YYYY-MM-DD HH:MM)",
                            "placeholder": "e.g., 1990-05-15 10:30",
                        },
                    }
                )
            else:
                birth_date_response = self.valves.birth_date

            # If using custom date but none provided, ask for it
            if use_custom_date and not custom_date:
                await __event_emitter__(
                    self.create_message("status", "Requesting custom current date...")
                )
                custom_date = await __event_call__(
                    {
                        "type": "input",
                        "data": {
                            "title": "Custom Current Date",
                            "message": "Enter custom current date (YYYY-MM-DD HH:MM)",
                            "placeholder": "e.g., 2025-04-17 14:30",
                        },
                    }
                )

            # Update status
            await __event_emitter__(
                self.create_message(
                    "status", "Parsing input dates and configuring time zones..."
                )
            )

            try:
                # Log selected options for debugging
                options_info = (
                    f"Selected options - Timezone: {timezone_response}, "
                    f"DST Enabled: {account_for_dst}, "
                    f"Using Custom Date: {use_custom_date}"
                )
                await __event_emitter__(self.create_message("status", options_info))
                await asyncio.sleep(2)  # Brief pause to show options

                # Parse birth date with timezone if DST is enabled
                birth_datetime = parse_datetime_with_timezone(
                    birth_date_response, timezone_response if account_for_dst else None
                )

                # Get current date - either custom or system time
                if use_custom_date and custom_date:
                    current_datetime = parse_datetime_with_timezone(
                        custom_date, timezone_response if account_for_dst else None
                    )
                else:
                    # Use system time with selected timezone
                    current_datetime = get_current_datetime(
                        timezone_response if account_for_dst else None
                    )

                # Handle case where one datetime has timezone and the other doesn't
                if (
                    birth_datetime.tzinfo is None
                    and current_datetime.tzinfo is not None
                ):
                    # If birth date doesn't have timezone but current does, apply current's timezone to birth
                    birth_datetime = birth_datetime.replace(
                        tzinfo=current_datetime.tzinfo
                    )
                elif (
                    birth_datetime.tzinfo is not None
                    and current_datetime.tzinfo is None
                ):
                    # If current date doesn't have timezone but birth does, apply birth's timezone to current
                    current_datetime = current_datetime.replace(
                        tzinfo=birth_datetime.tzinfo
                    )

                # Display the dates being used for calculation with timezone info
                tz_info = f" ({timezone_response})" if timezone_response else ""
                dst_info = " with DST" if account_for_dst else " without DST"

                date_info = (
                    f"Using birth date: {birth_datetime.strftime('%Y-%m-%d %H:%M %Z')} and "
                    f"current time: {current_datetime.strftime('%Y-%m-%d %H:%M %Z')}{tz_info}{dst_info}"
                )
                await __event_emitter__(self.create_message("status", date_info))
                await asyncio.sleep(5)  # Show this info for 5 seconds

            except ValueError as e:
                error_message = f"Error parsing dates: {str(e)}. Please check your format (YYYY-MM-DD HH:MM)."
                await __event_emitter__(
                    self.create_message(
                        "status", error_message, status="error", done=True
                    )
                )

                # Mark operation as complete
                self.is_operation_complete = True

                # Schedule auto-close on error too
                if self.valves.AUTO_CLOSE_OUTPUT:
                    self.close_task = asyncio.create_task(self.close_emitter_output())

                return {"error": error_message}

            # Update status for calculation - This will be replaced with the result
            calculating_status = self.create_message(
                "status",
                "Calculating age components and space travel distance...",
                status="in_progress",
            )
            await __event_emitter__(calculating_status)

            # Add a longer delay to make the status visible
            await asyncio.sleep(5)  # Increased delay for better visibility

            years, months, days, hours, minutes = calculate_age_components(
                birth_datetime, current_datetime
            )

            # Calculate space travel distance
            space_distance = calculate_space_travel(years, months, days, hours, minutes)

            # Format the distance in a readable way
            formatted_distance = format_distance(space_distance)

            # Format the output as a single line for status (removed prefix)
            output_message = f"✨ Time Alive! ✨ 🎂 Years: {years}, Months: {months} (approximate), Days: {days}, Hours: {hours}, Minutes: {minutes} | Space Travel: {formatted_distance}"

            # ONLY update the status with the result - NO MESSAGE event
            result_status = {
                "type": "status",
                "message_id": calculating_status[
                    "message_id"
                ],  # Use the same message ID to update
                "data": {
                    "status": "complete",
                    "description": output_message,
                    "done": True,
                    "message_id": calculating_status["message_id"],
                },
            }
            await __event_emitter__(result_status)

            # Mark operation as complete
            self.is_operation_complete = True

            # Schedule auto-close if enabled (now using longer delay)
            if self.valves.AUTO_CLOSE_OUTPUT:
                # Create a task to close the output after a delay
                self.close_task = asyncio.create_task(self.close_emitter_output())

            return {
                "age": {
                    "years": years,
                    "months": months,
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "birth_date": birth_datetime.strftime("%Y-%m-%d %H:%M %Z"),
                    "current_date": current_datetime.strftime("%Y-%m-%d %H:%M %Z"),
                    "timezone": (
                        str(timezone_response)
                        if timezone_response
                        else "System default"
                    ),
                    "dst_enabled": account_for_dst,
                    "space_travel_distance_km": space_distance,
                    "space_travel_formatted": formatted_distance,
                }
            }

        except Exception as e:
            # Error message
            error_message = f"Error calculating age: {str(e)}"
            await __event_emitter__(
                self.create_message("status", error_message, status="error", done=True)
            )

            # Mark operation as complete even on error
            self.is_operation_complete = True

            # Schedule auto-close on error too
            if self.valves.AUTO_CLOSE_OUTPUT:
                self.close_task = asyncio.create_task(self.close_emitter_output())

            return {"error": str(e)}


# Example of how you might run this outside of Open WebUI (for testing)
if __name__ == "__main__":

    async def mock_event_emitter(event):
        print(f"Event: {event}")

    async def mock_event_call(event_data):
        print(f"Event Call: {event_data}")
        # Mock user responses based on what's being asked
        if "Birth Date" in str(event_data):
            return "1990-05-15 10:30"
        elif "Custom Current Date" in str(event_data):
            return "2025-04-17 14:30"
        return "user input"  # Default mock user input

    async def main():
        action_instance = Action()

        # Set Valves values directly to simulate UI input
        action_instance.valves.timezone = "America/New_York"
        action_instance.valves.account_for_dst = True
        action_instance.valves.use_custom_current_date = False
        action_instance.valves.birth_date = "1990-05-15 10:30"

        print("Testing with Valves pre-filled:")
        result = await action_instance.action(
            body={},
            __user__="test_user",
            __event_emitter__=mock_event_emitter,
            __event_call__=mock_event_call,
        )
        print(f"Action Result: {result}")

        print("\nTesting with custom current date:")
        action_instance.valves.use_custom_current_date = True
        action_instance.valves.custom_current_date = "2025-04-17 14:30"

        result = await action_instance.action(
            body={},
            __user__="test_user",
            __event_emitter__=mock_event_emitter,
            __event_call__=mock_event_call,
        )
        print(f"Action Result with custom date: {result}")

    asyncio.run(main())
