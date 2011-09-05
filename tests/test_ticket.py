import unittest

from cartman import ticket


class TicketUnitTest(unittest.TestCase):

    def test_ticket_format_id(self):
        t = ticket.Ticket()
        self.assertEquals(t.format_id(), "#0.")
        t.id = 255
        self.assertEquals(t.format_id(), "#255.")

    def test_ticket_format_title(self):
        t = ticket.Ticket()
        t.id = 255
        t.summary = "meh"
        t.reporter = "jcarmack"
        self.assertEquals(t.format_title(), "#255. meh (jcarmack)")

    def test_ticket_factory(self):
        t = ticket.factory({
            "id": "245",
            "summary": "meh",
            "reporter": "douche",
            "description": "clean all the things",
        })

        self.assertEquals(t.id, 245)
        self.assertEquals(t.summary, "meh")
        self.assertEquals(t.reporter, "douche")
        self.assertEquals(t.description, "clean all the things")

    def test_ticket_factory_alt(self):
        t = ticket.factory({
            "ticket": "123",
            "_reporter": "douche",
        })

        self.assertEquals(t.id, 123)
        self.assertEquals(t.reporter, "douche")
