import requests

def get_comp_id():
    comp_id = input("Please give the id of the Competition: ")
    base_url = f"https://www.worldcubeassociation.org/api/v0/competitions/{comp_id}/wcif/public"
    response = requests.get(base_url)  # Zeile doppelt — eine löschen!
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Fehlercode: {response.status_code}")
        return None


def get_event(data):
    events=[]
    for event in data["events"]:
       events.append(event["id"])
    return events
    
    def get_event_name(event_id):
       names = {
        "333":    "3x3x3 Cube",
        "222":    "2x2x2 Cube",
        "444":    "4x4x4 Cube",
        "555":    "5x5x5 Cube",
        "666":    "6x6x6 Cube",
        "777":    "7x7x7 Cube",
        "333oh":  "3x3 One-Handed",
        "333bf":  "3x3 Blindfolded",
        "444bf":  "4x4 Blindfolded",
        "555bf":  "5x5 Blindfolded",
        "333mbf": "Multi-Blind",
        "333fm":  "Fewest Moves",
        "clock":  "Clock",
        "minx":   "Megaminx",
        "pyram":  "Pyraminx",
        "skewb":  "Skewb",
        "sq1":    "Square-1"
    }
    return names.get(event_id, event_id)

  