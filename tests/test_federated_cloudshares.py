from NextCloud import ShareType

from .base import BaseTestCase, NextCloud, NEXTCLOUD_URL


class TestFederatedCloudShares(BaseTestCase):

    def setUp(self):
        super(TestFederatedCloudShares, self).setUp()
        user_password = self.get_random_string(length=8)
        self.user_username = self.create_new_user('shares_user_', password=user_password)
        self.nxc_local = self.nxc_local = NextCloud(NEXTCLOUD_URL, self.user_username, user_password, js=True)
        # make user admin
        self.nxc.add_to_group(self.user_username, 'admin')

    def tearDown(self):
        self.nxc.delete_user(self.user_username)

    def test_create_federated_cloudhsare(self):
        share_path = "Documents"

        res = self.nxc_local.create_share(share_path,
                                          share_type=ShareType.FEDERATED_CLOUD_SHARE.value,
                                          share_with="admin@app:80")
        assert res['ocs']['meta']['statuscode'] == self.SHARE_API_SUCCESS_CODE
