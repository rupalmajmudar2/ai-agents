import json
import os
from mcp.server.fastmcp import FastMCP
from typing import List, Dict

# File path for JSON storage
DATA_FILE = "family_and_friends.json"

# Load data from JSON file
def load_data() -> Dict:
    """Load family and friends data from a JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Save data to JSON file
def save_data(data: Dict) -> None:
    """Save family and friends data to a JSON file."""
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Initialize data
family_and_friends = load_data()

# Create MCP server
mcp = FastMCP("FamilyAndFriendsMcpServer")

# Tool: List all family and friends
@mcp.tool()
def list_family_and_friends() -> str:
    """List all family and friends with their details."""
    if not family_and_friends:
        return "No family or friends found."
    
    result = []
    for ff_id, details in family_and_friends.items():
        family_members = ', '.join(details["family_members"])
        important_dates = ', '.join(f"{key}: {value}" for key, value in details["important_dates"].items())
        result.append(
            f"FFId: {ff_id}, Name: {details['firstname']} {details['lastname']}, "
            f"Family Members: {family_members}, Important Dates: {important_dates}"
        )
    return "\n".join(result)

# Tool: Add a family or friend member
@mcp.tool()
def add_family_or_friend(ff_id: str, firstname: str, lastname: str, family_members: List[str], important_dates: Dict[str, str]) -> str:
    """
    Add a new family or friend member to the list.
    family_members: List of family member descriptions (e.g., ["wife: Jyoti", "son: Ankush"])
    important_dates: Dictionary of important dates (e.g., {"dob": "15-04-1968", "wedding_anniversary": "24-12-1991"})
    """
    if ff_id in family_and_friends:
        return f"FFId {ff_id} already exists."
    
    family_and_friends[ff_id] = {
        "firstname": firstname,
        "lastname": lastname,
        "family_members": family_members,
        "important_dates": important_dates
    }
    save_data(family_and_friends)
    return f"Family/Friend member {firstname} {lastname} added successfully with FFId {ff_id}."

# Tool: Remove a family or friend member
@mcp.tool()
def remove_family_or_friend(ff_id: str) -> str:
    """Remove a family or friend member from the list."""
    if ff_id not in family_and_friends:
        return f"FFId {ff_id} not found."
    
    removed_member = family_and_friends.pop(ff_id)
    save_data(family_and_friends)
    return f"Family/Friend member {removed_member['firstname']} {removed_member['lastname']} removed successfully."

# Tool: Find the closest important date
@mcp.tool()
def find_closest_important_date(date: str = None) -> str:
    """
    Find the family or friend member with the closest important date to the given date.
    If no date is provided, defaults to today.
    """
    from datetime import datetime, timedelta

    if not family_and_friends:
        return "No family or friends found."

    # Parse the input date or use today's date
    today = datetime.today()
    target_date = datetime.strptime(date, "%Y-%m-%d") if date else today

    closest_member = None
    closest_date = None
    min_diff = timedelta.max

    for ff_id, details in family_and_friends.items():
        for event, event_date in details["important_dates"].items():
            try:
                # Parse the event date
                event_datetime = datetime.strptime(event_date, "%d-%m-%Y")
                # Calculate the difference in days
                diff = abs((event_datetime - target_date).days)
                if diff < min_diff:
                    min_diff = diff
                    closest_member = f"{details['firstname']} {details['lastname']} ({event}: {event_date})"
                    closest_date = event_datetime
            except ValueError:
                continue  # Skip invalid dates

    if closest_member:
        return f"The closest important date is for {closest_member} on {closest_date.strftime('%d-%m-%Y')}."
    return "No valid important dates found."

if __name__ == "__main__":
    mcp.run()