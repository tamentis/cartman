
class Ticket:

    def __init__(self):
        self.id = 0
        self.summary = "Summary N/A"
        self.reporter = "Reporter N/A"
        self.description = "Description N/A"

    def format_id(self):
        return "#%d." % self.id

    def format_title(self):
        return "%(id_fmt)s %(summary)s (%(reporter)s)" % {
            "id_fmt": self.format_id(),
            "summary": self.summary,
            "reporter": self.reporter,
        }


def factory(ticket_dict):
    ticket = Ticket()

    if "id" in ticket_dict:
        ticket.id = int(ticket_dict["id"])
    elif "ticket" in ticket_dict:
        ticket.id = int(ticket_dict["ticket"])

    if "summary" in ticket_dict:
        ticket.summary = ticket_dict["summary"]

    if "_reporter" in ticket_dict:
        ticket.reporter = ticket_dict["_reporter"]
    elif "reporter" in ticket_dict:
        ticket.reporter = ticket_dict["reporter"]

    if "description" in ticket_dict:
        ticket.description = ticket_dict["description"]

    return ticket
