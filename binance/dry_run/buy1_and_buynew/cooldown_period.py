import logging
from datetime import datetime, timedelta

from freqtrade.constants import LongShort
from freqtrade.persistence import Trade
from freqtrade.plugins.protections import IProtection, ProtectionReturn


logger = logging.getLogger(__name__)


class CooldownPeriod(IProtection):
    has_global_stop: bool = False
    has_local_stop: bool = True

    def _reason(self) -> str:
        """
        LockReason to use
        """
        return f"Cooldown period for {self.unlock_reason_time_element}."

    def short_desc(self) -> str:
        """
        Short method description - used for startup messages
        """
        return f"{self.name} - Cooldown period {self.unlock_reason_time_element}."

    def _cooldown_period(self, pair: str, date_now: datetime) -> ProtectionReturn | None:
        """
        Get last trade for this pair
        """
        look_back_until = date_now - timedelta(minutes=self._lookback_period)
        # filters = [
        #     Trade.is_open.is_(False),
        #     Trade.close_date > look_back_until,
        #     Trade.pair == pair,
        # ]
        # trade = Trade.get_trades(filters).first()
        trades = Trade.get_trades_proxy(pair=pair, is_open=False, close_date=look_back_until)
        if trades:
            # Get latest trade
            # Ignore type error as we know we only get closed trades.
            trade = sorted(trades, key=lambda t: t.close_date)[-1]  # type: ignore
            if trade.exit_reason == "stop_loss":
                self.log_once(f"Cooldown for {pair} {self.unlock_reason_time_element}.", logger.info)
                until = self.calculate_lock_end([trade])

                return ProtectionReturn(
                    lock=True,
                    until=until,
                    reason=self._reason(),
                )
            else:
                return None

        return None

    def global_stop(self, date_now: datetime, side: LongShort) -> ProtectionReturn | None:
        """
        Stops trading (position entering) for all pairs
        This must evaluate to true for the whole period of the "cooldown period".
        :return: Tuple of [bool, until, reason].
            If true, all pairs will be locked with <reason> until <until>
        """
        # Not implemented for cooldown period.
        return None

    def stop_per_pair(
        self, pair: str, date_now: datetime, side: LongShort
    ) -> ProtectionReturn | None:
        """
        Stops trading (position entering) for this pair
        This must evaluate to true for the whole period of the "cooldown period".
        :return: Tuple of [bool, until, reason].
            If true, this pair will be locked with <reason> until <until>
        """
        return self._cooldown_period(pair, date_now)
