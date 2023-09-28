import discord

from discord.ui import Modal, TextInput
from components.UpdatePayModalCallback import UpdatePayModalCallback

"""
Text inputs are an interactive component that render on modals. They can be used to collect short-form or long-form text -> https://discord.com/developers/docs/interactions/message-components#text-inputs
This object must be inherited to create a modal popup window within discord -> https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=modal#modal
"""

class UpdatePayModal(Modal, title='Questionnaire Response'):

    amount = TextInput(label='Amount To Add', custom_id="amount", required=True, style=discord.TextStyle.short, placeholder="0")
    name = TextInput(label="Cleaner's First Name OR Listing Nickname", custom_id="name", required=True, style=discord.TextStyle.short, placeholder="eg. Raiden/Clover")

    async def on_submit(self, interaction: discord.Interaction):
        update_pay_cb = UpdatePayModalCallback()
        await update_pay_cb.update_pay_modal_callback(interaction=interaction, name=self.name, amount=self.amount)
