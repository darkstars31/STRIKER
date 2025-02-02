import asyncio
from collections import Counter
from typing import List

import disnake
from tabulate import tabulate

from domain.domain import Death, Job, Player

from .area import places
from .config import CT_COIN, T_COIN


class AbortButton(disnake.ui.Button):
    def __init__(self, *, callback, style=disnake.ButtonStyle.danger, label="Abort", row=0):
        super().__init__(style=style, label=label, row=row)
        self._callback = callback

    async def callback(self, inter: disnake.MessageInteraction):
        asyncio.create_task(self._callback(inter))


class PlayerButton(disnake.ui.Button):
    def __init__(self, callback, player, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callback = callback
        self.player = player

    async def callback(self, inter: disnake.MessageInteraction):
        self.view.stop()
        asyncio.create_task(self._callback(inter, self.player))


class PlayerView(disnake.ui.View):
    def __init__(
        self,
        *,
        job: Job,
        player_callback,
        abort_callback,
        timeout_callback,
        timeout=180.0,
    ):
        super().__init__(timeout=timeout)
        self.job = job
        self.player_callback = player_callback
        self.abort_callback = abort_callback
        self.on_timeout = timeout_callback

        # team one starts as T, team two starts as CT
        team_one, team_two = job.demo.teams

        for row, players in enumerate([team_two, team_one]):
            label = f"Team {row + 1}"
            self.add_item(
                disnake.ui.Button(
                    style=disnake.ButtonStyle.secondary,
                    label=label,
                    disabled=True,
                    row=row * 2,
                )
            )

            for player in players:
                self.add_item(
                    PlayerButton(
                        callback=player_callback,
                        player=player,
                        label=player.name,
                        style=disnake.ButtonStyle.primary,
                        row=(row * 2) + 1,
                    )
                )

        self.add_item(AbortButton(callback=self.abort_callback))


class RoundButton(disnake.ui.Button):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callback = callback

    async def callback(self, inter: disnake.MessageInteraction):
        self.view.stop()
        asyncio.create_task(self._callback(inter, int(self.label)))


class RoundView(disnake.ui.View):
    def __init__(
        self,
        *,
        round_callback,
        reselect_callback,
        abort_callback,
        timeout_callback,
        job: Job,
        embed_factory,
        player: Player,
        timeout=180.0,
    ):
        super().__init__(timeout=timeout)

        self.round_callback = round_callback
        self.reselect_callback = reselect_callback
        self.abort_callback = abort_callback
        self.on_timeout = timeout_callback
        self.timeout_callback = timeout_callback
        self.job = job
        self.embed_factory = embed_factory
        self.demo = job.demo
        self.player = player
        self.player_team = self.demo.get_player_team(player)
        self.kills: List[Death] = self.demo.get_player_kills(player)
        self.round_buttons = list()

        self.first_half.emoji = T_COIN if self.player_team == 0 else CT_COIN
        self.second_half.emoji = CT_COIN if self.player_team == 0 else T_COIN

        self.highlights = {
            True: self.create_table(True),
            False: self.create_table(False),
        }

        for round_id in range(1, self.demo.halftime + 1):
            button = RoundButton(
                callback=round_callback,
                style=disnake.ButtonStyle.primary,
                label="placeholder",
                row=((round_id - 1) // 5) + 1,
            )

            self.round_buttons.append(button)
            self.add_item(button)

    @disnake.ui.button(row=0)
    async def first_half(self, button: disnake.Button, inter: disnake.MessageInteraction):
        embed = await self.set_half(True)

        await inter.response.edit_message(
            content=None,
            embed=embed,
            view=self,
        )

    @disnake.ui.button(row=0)
    async def second_half(self, button: disnake.Button, inter: disnake.MessageInteraction):
        embed = await self.set_half(False)

        await inter.response.edit_message(
            content=None,
            embed=embed,
            view=self,
        )

    @disnake.ui.button(style=disnake.ButtonStyle.secondary, label="Select another player", row=0)
    async def reselect(self, button: disnake.Button, inter: disnake.MessageInteraction):
        self.stop()
        asyncio.create_task(self.reselect_callback(inter))

    @disnake.ui.button(style=disnake.ButtonStyle.danger, label="Abort", row=0)
    async def abort(self, button: disnake.Button, inter: disnake.MessageInteraction):
        self.stop()
        asyncio.create_task(self.abort_callback(inter))

    def round_range(self, first_half):
        halftime = self.demo.halftime
        return range(
            1 if first_half else halftime + 1,
            (halftime if first_half else halftime * 2) + 1,
        )

    def create_table(self, first_half):
        demo = self.job.demo
        round_range = self.round_range(first_half)
        map_area = places.get(demo.map, None)
        data = []

        for round_id in round_range:
            kills = self.kills.get(round_id, None)
            if kills is not None:
                data.append(demo.kills_info(round_id, kills, map_area))

        if not data:
            return "This player got zero kills this half."
        else:
            return tabulate(
                tabular_data=data,
                colalign=("left", "left", "left"),
                tablefmt="plain",
            )

    async def set_half(self, first_half):
        enabled_style = disnake.ButtonStyle.success
        disabled_style = disnake.ButtonStyle.primary

        self.first_half.disabled = first_half
        self.second_half.disabled = not first_half
        self.first_half.style = enabled_style if first_half else disabled_style
        self.second_half.style = disabled_style if first_half else enabled_style

        round_range = self.round_range(first_half)
        max_rounds = self.demo.round_count

        for round_id, button in zip(round_range, self.round_buttons):
            button.label = str(round_id)

            if round_id > max_rounds:
                button.disabled = True
                button.style = disnake.ButtonStyle.secondary
            else:
                button.disabled = round_id not in self.kills
                button.style = disnake.ButtonStyle.primary

        embed = self.embed_factory()

        table = self.highlights[first_half]
        half_one = "T" if self.player_team == 0 else "CT"
        half_two = "CT" if self.player_team == 0 else "T"
        team = half_one if first_half else half_two

        # embed.title = 'Select a round to render'

        embed.description = (
            f"Table of {self.player.name}'s frags on the {team} side.\n"
            f"```{table}```\n"
            "Click a round number below to record a highlight.\n"
            "Click the 'CT' or 'T' coins to show frags from the other half."
        )

        return embed
