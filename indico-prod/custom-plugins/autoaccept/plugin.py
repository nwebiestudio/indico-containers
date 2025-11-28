from indico.core.plugins import IndicoPlugin
from indico.core.signals import event as event_signals
from indico.modules.events.abstracts.operations import judge_abstract
from indico.modules.users.util import get_system_user

# ID мероприятий, в которых включено авто-принятие
ALLOWED_EVENTS = {5}  # замените на свои


class AutoAcceptAbstractsPlugin(IndicoPlugin):
    """Automatically accepts abstracts for selected events."""

    def init(self):
        super().init()
        event_signals.abstract_created.connect(self._on_abstract_created, sender=None)

    def _on_abstract_created(self, sender, abstract, **kwargs):
        event = sender

        if event.id not in ALLOWED_EVENTS:
            return

        try:
            judge = get_system_user()

            judge_abstract(
                abstract=abstract,
                data={},
                judgment="accept",
                user=judge,
                contrib_session=None,
                merge_persons=False,
                send_notifications=True,
            )

            self.logger.info(
                f"Auto-accepted abstract {abstract.id} for event {event.id}"
            )

        except Exception:
            self.logger.exception(
                f"Failed to auto-accept abstract {abstract.id} (event {event.id})"
            )
