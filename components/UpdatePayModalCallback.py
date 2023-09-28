import asyncio
import logging

import discord
from utils.database.DatabaseMultiOperations import DatabaseMultiOperations
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.OrganizeGuestyData import OrganizeGuestyData


class UpdatePayModalCallback:
    def __init__(self):
        self.guesty_user = GuestyUserRequests()
        self.guesty_listing = GuestyListingRequests()
        self.ogd = OrganizeGuestyData()

    async def update_pay_modal_callback(self, interaction: discord.Interaction, name, amount):
        """
        TODO:
            Update payment for particular assignee (user), or particular listing (task)
            create a new field in user and task with name of adjustment
            if listing is adjusted add amount to listing
            if user is adjusted add amount to user
        """
        try:
            await interaction.response.defer()
            new_amount = None
            new_name = None
            try:
                str_amount = str(amount)
                new_amount = int(str_amount)
                new_name = str(name)
            except Exception as e:
                await interaction.followup.send(f'Amount must be a decimal value!', ephemeral=True)
                return

            find_guesty_user = await self.guesty_user.search_a_user(username=new_name)
            db = DatabaseMultiOperations()

            # Listing update
            # ===============================================================================================================
            if find_guesty_user is None:
                find_all_listings = await self.guesty_listing.get_all_listing()
                find_listing = next((l for l in find_all_listings if l['nickname'].lower() == new_name.strip().lower()), None)
                if find_listing is None:
                    await interaction.followup.send(f'No listing or user found with the name of {new_name}!', ephemeral=True)
                    return
                adjust_data = self.ogd.adjust_insert_data(amount=new_amount, guesty_listing_id=find_listing['_id'])
                await db.insert_one_adjust(data=adjust_data)
                await interaction.followup.send(f'A task has been updated!', ephemeral=True)
                return

            # User update
            # ===============================================================================================================
            guesty_user_id = find_guesty_user["_id"]
            adjust_data = self.ogd.adjust_insert_data(amount=new_amount, guesty_user_id=guesty_user_id)
            await asyncio.gather(
                db.insert_one_adjust(data=adjust_data),
                interaction.followup.send(f'A task has been updated!', ephemeral=True)
            )
        except Exception as e:
            logging.error(e)
