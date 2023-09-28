from controllers.ControllerBase import ControllerBase
from utils.database.DatabaseManagement import DatabaseManagement
from utils.OrganizeGuestyData import OrganizeGuestyData
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from seeds.Initializer import Initializer
from controllers.PayCalcController import PayCalcController


class StartupController(ControllerBase):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.count = 1
        self.guesty_task = GuestyTaskRequests()
        self.initializer = Initializer(client=client)
        self.pay_calc = PayCalcController(client=client)
        self.db = DatabaseManagement()
        self.ogd = OrganizeGuestyData()


    async def initialize(self):
        await self.initializer.run(daily=False)
        await self.pay_calc.run(daily=False)
