# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

import yc.stepcstep


class YcStepcstepLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=yc.stepcstep)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'yc.stepcstep:default')


YC_STEPCSTEP_FIXTURE = YcStepcstepLayer()

YC_STEPCSTEP_INTEGRATION_TESTING = IntegrationTesting(
    bases=(YC_STEPCSTEP_FIXTURE,),
    name='YcStepcstepLayer:IntegrationTesting',
)

YC_STEPCSTEP_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(YC_STEPCSTEP_FIXTURE,),
    name='YcStepcstepLayer:FunctionalTesting',
)
