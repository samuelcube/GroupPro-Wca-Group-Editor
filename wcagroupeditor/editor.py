import requests
import random
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm


def load_comp_data():
    comp_id = input("Please give the id of the Competition: ")
    base_url = f"https://www.worldcubeassociation.org/api/v0/competitions/{comp_id}/wcif/public"
    response = requests.get(base_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Fehlercode: {response.status_code}")
        return None


def get_events(data):
    events = []
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


def get_competitors(data):
    competitors = []
    for person in data["persons"]:
        if person["registration"]["status"] == "accepted":
            competitors.append({
                "name":         person["name"],
                "wcaId":        person.get("wcaId", ""),
                "registrantId": person.get("registrantId", "")
            })
    return competitors


def get_competitors_for_event(data, event_id):
    competitors = []
    for person in data["persons"]:
        if person["registration"]["status"] == "accepted":
            if event_id in person["registration"]["eventIds"]:

                best_time = None
                for pb in person.get("personalBests", []):
                    if pb["eventId"] == event_id and pb["type"] == "average":
                        best_time = pb["best"]

                competitors.append({
                    "name":         person["name"],
                    "wcaId":        person.get("wcaId", ""),
                    "registrantId": person.get("registrantId", ""),
                    "time":         best_time or 999999
                })

    # Langsame zuerst, Schnelle zuletzt
    competitors.sort(key=lambda x: x["time"], reverse=True)

    return competitors


def create_groups(competitors, group_count):
    groups = defaultdict(list)

    for i, competitor in enumerate(competitors):
        group = (i % group_count) + 1
        groups[group].append(competitor)

    return groups


def assign_staff(groups, scramblers, runners, judges):
    result = {}

    for group_nr, members in groups.items():

        available = []
        for other_group_nr, other_members in groups.items():
            if other_group_nr != group_nr:
                available.extend(other_members)

        # Nach Zeit sortieren
        available.sort(key=lambda x: x["time"])

        # Schnellste für Scramblers → top pool mischen
        top_pool = available[:scramblers * 3]
        random.shuffle(top_pool)
        assigned_scramblers = top_pool[:scramblers]

        # Langsamste für Runners und Judges → bottom pool mischen
        available_rest = available[scramblers:]
        bottom_pool    = list(reversed(available_rest))
        bottom_pool    = bottom_pool[:(runners + judges) * 3]
        random.shuffle(bottom_pool)
        assigned_runners = bottom_pool[:runners]
        assigned_judges  = bottom_pool[runners:runners + judges]

        result[group_nr] = {
            "competitors": members,
            "scramblers":  assigned_scramblers,
            "runners":     assigned_runners,
            "judges":      assigned_judges
        }

    return result


def print_groups(staff_groups, scramblers, runners, judges):
    for group_nr, data in staff_groups.items():
        print(f"\n{'='*30}")
        print(f"Gruppe {group_nr}:")

        print(f"\n  Competitors ({len(data['competitors'])}):")
        for c in data["competitors"]:
            print(f"    {c['registrantId']} - {c['name']}")

        print(f"\n  Scramblers ({scramblers}):")
        for c in data["scramblers"]:
            print(f"    {c['registrantId']} - {c['name']}")

        print(f"\n  Runner ({runners}):")
        for c in data["runners"]:
            print(f"    {c['registrantId']} - {c['name']}")

        print(f"\n  Judges ({judges}):")
        for c in data["judges"]:
            print(f"    {c['registrantId']} - {c['name']}")


def export_pdf(staff_groups, event_name, filename="{comp_id}_gruppen.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()

    # Eigene Styles
    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold",
                                 spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
    group_style = ParagraphStyle("group", fontSize=13, fontName="Helvetica-Bold",
                                 spaceAfter=4, textColor=colors.HexColor("#16213e"),
                                 spaceBefore=14)
    section_style = ParagraphStyle("section", fontSize=10, fontName="Helvetica-Bold",
                                   spaceAfter=2, textColor=colors.HexColor("#0f3460"))

    story = []

    # Titel
    story.append(Paragraph(f"Gruppenplan - {event_name}", title_style))
    story.append(Paragraph(f"{len(staff_groups)} Gruppen", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    for group_nr, data in staff_groups.items():
        story.append(Paragraph(f"Gruppe {group_nr}", group_style))

        # Competitors Tabelle
        story.append(Paragraph("Competitors", section_style))
        comp_data = [["#", "Name", "WCA ID"]]
        for c in data["competitors"]:
            comp_data.append([c["registrantId"], c["name"], c["wcaId"] or "-"])

        comp_table = Table(comp_data, colWidths=[1.5*cm, 10*cm, 4*cm])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
            ("GRID",           (0, 0), (-1, -1), 0.3, colors.grey),
            ("PADDING",        (0, 0), (-1, -1), 4),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 0.3*cm))

        # Staff Tabelle
        story.append(Paragraph("Staff", section_style))
        staff_data = [["Rolle", "Name", "WCA ID"]]
        for c in data["scramblers"]:
            staff_data.append(["Scrambler", c["name"], c["wcaId"] or "-"])
        for c in data["runners"]:
            staff_data.append(["Runner", c["name"], c["wcaId"] or "-"])
        for c in data["judges"]:
            staff_data.append(["Judge", c["name"], c["wcaId"] or "-"])

        staff_table = Table(staff_data, colWidths=[3*cm, 8.5*cm, 4*cm])

        # Basis Style
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0),  colors.HexColor("#0f3460")),  # Header
            ("TEXTCOLOR",  (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",   (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 8),
            ("GRID",       (0, 0), (-1, -1), 0.3, colors.grey),
            ("PADDING",    (0, 0), (-1, -1), 4),
        ]

        # Scramblers → Orange
        for row in range(1, len(data["scramblers"]) + 1):
            table_style.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#fff3e0")))

        # Runners → Grün
        runner_start = len(data["scramblers"]) + 1
        for row in range(runner_start, runner_start + len(data["runners"])):
            table_style.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#e8f5e9")))

        # Judges → Blau
        judge_start = runner_start + len(data["runners"])
        for row in range(judge_start, judge_start + len(data["judges"])):
            table_style.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#e3f2fd")))

        staff_table.setStyle(TableStyle(table_style))
        story.append(staff_table)
        story.append(Spacer(1, 0.4*cm))

    doc.build(story)
    print(f"\nPDF gespeichert: {filename}")


# ==================================================
# Ausführung
# ==================================================

data_comp = load_comp_data()

if data_comp:
    events = get_events(data_comp)
    remaining_events = events.copy()

    while True:
        print("\nEvents:")
        for i, event in enumerate(remaining_events):
            count = len(get_competitors_for_event(data_comp, event))
            print(f"  {i+1}. {get_event_name(event)} ({count} Competitors)")
        print(f"  0. Beenden")

        choice = int(input("\nWelches Event? Nummer eingeben: "))

        if choice == 0:
            print("Programm beendet.")
            break

        event_id    = remaining_events[choice - 1]
        group_count = int(input("Wie viele Gruppen? "))
        scramblers  = int(input("Wie viele Scramblers pro Gruppe? "))
        runners     = int(input("Wie viele Runner pro Gruppe? "))
        judges      = int(input("Wie viele Judges pro Gruppe? "))

        competitors  = get_competitors_for_event(data_comp, event_id)

        print(f"\n{len(competitors)} Competitors für {get_event_name(event_id)} geladen")

        groups       = create_groups(competitors, group_count)
        staff_groups = assign_staff(groups, scramblers, runners, judges)

        print_groups(staff_groups, scramblers, runners, judges)

        # PDF exportieren
        pdf_name = f"{event_id}_gruppen.pdf"
        export_pdf(staff_groups, get_event_name(event_id), filename=pdf_name)

        input("\nWeiter mit Enter...")

        remaining_events.remove(event_id)

        if not remaining_events:
            print("\nAlle Events abgeschlossen!")
            break