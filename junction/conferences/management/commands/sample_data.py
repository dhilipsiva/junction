from __future__ import print_function

# Standard Library
import datetime
import random

# Third Party Stuff
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now
from junction.base import constants
from junction.conferences.models import Conference
from junction.proposals.models import ProposalSection, ProposalType
from sampledatahelper.helper import SampleDataHelper

NUM_USERS = getattr(settings, "SAMPLE_DATA_NUM_USERS", 10)
NUM_CONFERENCES = getattr(settings, "SAMPLE_DATA_NUM_CONFERENCES", 4)
NUM_EMPTY_CONFERENCES = getattr(settings, "SAMPLE_DATA_NUM_EMPTY_CONFERENCES", 2)
NUM_PROPOSAL_SECTIONS = getattr(settings, "NUM_PROPOSAL_SECTIONS", 5)
NUM_PROPOSAL_TYPES = getattr(settings, "NUM_PROPOSAL_TYPES", 8)


class Command(BaseCommand):
    sd = SampleDataHelper(seed=12345678901)

    @transaction.atomic
    def handle(self, *args, **options):

        self.users = []

        # Update site url
        print('  Updating domain to localhost:8000')
        site = Site.objects.get_current()
        site.domain = 'localhost:8000'
        site.name = 'Local'
        site.save()

        # create superuser
        print('  Creating Superuser')
        self.create_user(is_superuser=True, username='admin', is_active=True)

        # create users
        print('  Creating sample Users')
        for x in range(NUM_USERS):
            self.users.append(self.create_user(counter=x))

        print('  Creating proposal sections')
        self.proposal_sections = self.create_proposal_sections()

        print('  Create proposal types')
        self.proposal_types = self.create_proposal_types()

        # create conferences
        print('  Creating sample Conferences')
        for x in range(NUM_CONFERENCES + NUM_EMPTY_CONFERENCES):
            conference = self.create_conference(x)

            if x < NUM_CONFERENCES:
                self.create_moderators(conference)
                self.create_propsoal_reviewers(conference)

                # attach proposal sections
                count = self.sd.int(1, len(self.proposal_sections))
                for section in random.sample(self.proposal_sections, count):
                    conference.proposal_sections.add(section)

                # attach proposal types
                count = self.sd.int(1, len(self.proposal_types))
                for proposal_type in random.sample(self.proposal_types, count):
                    conference.proposal_types.add(proposal_type)

    def create_proposal_sections(self):
        sections = []
        for count in range(NUM_PROPOSAL_SECTIONS):
            sections.append(ProposalSection.objects.create(**{
                'name': "Proposal Section %d" % count,
                'description': "Proposal Section %d description" % count,
                'active': self.sd.boolean()
            }))
        return sections

    def create_proposal_types(self):
        types = []
        for count in range(NUM_PROPOSAL_TYPES):
            types.append(ProposalType.objects.create(**{
                'name': "Proposal Type %d" % count,
                'description': "Proposal Section %d description" % count,
                'active': self.sd.boolean()
            }))
        return types

    def create_moderators(self, conference):
        moderators = []
        count = self.sd.int(1, len(self.users))
        for user in random.sample(self.users, count):
            moderators.append(conference.moderators.create(moderator=user, active=self.sd.boolean()))
        return moderators

    def create_propsoal_reviewers(self, conference):
        proposal_reviewers = []
        count = self.sd.int(1, len(self.users))
        for user in random.sample(self.users, count):
            proposal_reviewers.append(conference.proposal_reviewers.create(reviewer=user, active=self.sd.boolean()))
        return proposal_reviewers

    def create_conference(self, counter, start_date=None, end_date=None):
        start_date = start_date or now() + datetime.timedelta(random.randrange(-55, 55))
        end_date = end_date or start_date + datetime.timedelta(random.randrange(1, 4))
        conference = Conference.objects.create(name='%s Conference' % self.sd.words(1, 2).title(),
                                               description=self.sd.paragraph(),
                                               status=self.sd.choices_key(constants.CONFERENCE_STATUS_LIST),
                                               start_date=start_date,
                                               end_date=end_date,
                                               created_by=self.sd.choice(self.users),
                                               modified_by=self.sd.choice(self.users),
                                               )

        return conference

    def create_user(self, counter=None, username=None, email=None, **kwargs):
        counter = counter or self.sd.int()
        params = {
            "username": username or 'user{0}'.format(counter),
            "first_name": kwargs.get('first_name', self.sd.name("us", 1)),
            "last_name": kwargs.get('last_name', self.sd.surname("us", 1)),
            "email": email or self.sd.email(),
            "is_active": kwargs.get('is_active', self.sd.boolean()),
            "is_superuser": kwargs.get('is_superuser', False),
            "is_staff": kwargs.get('is_staff', kwargs.get('is_superuser', self.sd.boolean())),
        }
        user = get_user_model().objects.create(**params)
        user.set_password('123123')
        user.save()

        return user
