
import manilaclient.client
import manilaclient.v1.client

from tests import utils


class ClientTest(utils.TestCase):

    def test_get_client_class_v1(self):
        output = manilaclient.client.get_client_class('1')
        self.assertEqual(output, manilaclient.v1.client.Client)

    def test_get_client_class_unknown(self):
        self.assertRaises(manilaclient.exceptions.UnsupportedVersion,
                          manilaclient.client.get_client_class, '0')
