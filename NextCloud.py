import enum
import requests
import re
import types

PUBLIC_API_NAME_CLASS_MAP = dict()


class Requester(object):
    def __init__(self, endpoint, user, passwd, js=False):
        self.query_components = []

        self.to_json = js

        self.base_url = endpoint
        # GroupFolders.url = endpoint + "/ocs/v2.php/apps/groupfolders/folders"

        self.h_get = {"OCS-APIRequest": "true"}
        self.h_post = {"OCS-APIRequest": "true",
                       "Content-Type": "application/x-www-form-urlencoded"}
        self.auth_pk = (user, passwd)
        self.API_URL = None

    def rtn(self, resp):
        if self.to_json:
            return resp.json()
        else:
            return resp.content.decode("UTF-8")

    def get(self, url="", params=None):
        url = self.get_full_url(url)
        res = requests.get(url, auth=self.auth_pk, headers=self.h_get, params=params)
        return self.rtn(res)

    def post(self, url="", data=None):
        url = self.get_full_url(url)
        res = requests.post(url, auth=self.auth_pk, data=data, headers=self.h_post)
        return self.rtn(res)

    def put(self, url="", data=None):
        url = self.get_full_url(url)
        res = requests.put(url, auth=self.auth_pk, data=data, headers=self.h_post)
        return self.rtn(res)

    def delete(self, url="", data=None):
        url = self.get_full_url(url)
        res = requests.delete(url, auth=self.auth_pk, data=data, headers=self.h_post)
        return self.rtn(res)

    def get_full_url(self, additional_url=""):
        """
        Build full url for request to NextCloud api

        Construct url from self.base_url, self.API_URL, additional_url (if given), add format=json param if self.json

        :param additional_url: str
            add to url after api_url
        :return: str
        """
        if additional_url and not str(additional_url).startswith("/"):
            additional_url = "/{}".format(additional_url)

        if self.to_json:
            self.query_components.append("format=json")

        ret = "{base_url}{api_url}{additional_url}".format(
            base_url=self.base_url, api_url=self.API_URL, additional_url=additional_url)

        if self.to_json:
            ret += "?format=json"
        return ret


def nextcloud_method(method_to_wrap):
    class_name = method_to_wrap.__qualname__.split(".", 1)[0]
    PUBLIC_API_NAME_CLASS_MAP[method_to_wrap.__name__] = class_name
    return method_to_wrap


class NextCloud(object):

    def __init__(self, endpoint, user, password, js=False):
        self.query_components = []

        requester = Requester(endpoint, user, password, js)

        self.functionality = {
            "Apps": Apps(requester),
            "Group": Group(requester),
            "GroupFolders": GroupFolders(requester),
            "Share": Share(requester),
            "User": User(requester),
            "FederatedCloudShare": FederatedCloudShare(requester),
            "Activity": Activity(requester),
            "Notifications": Notifications(requester),
            "UserLDAP": UserLDAP(requester),
            "Capabilities": Capabilities(requester),
        }
        for name, location in PUBLIC_API_NAME_CLASS_MAP.items():
            setattr(self, name, getattr(self.functionality[location], name))


class WithRequester(object):

    API_URL = NotImplementedError

    def __init__(self, requester):
        self._requester = requester

    @property
    def requester(self):
        """ Get requester instance """
        # dynamically set API_URL for requester
        self._requester.API_URL = self.API_URL
        return self._requester


class Capabilities(WithRequester):
    API_URL = "/ocs/v1.php/cloud/capabilities"

    @nextcloud_method
    def get_capabilities(self):
        """ Obtain capabilities provided by the Nextcloud server and its apps """
        return self.requester.get()


class GroupFolders(WithRequester):
    API_URL = "/apps/groupfolders/folders"

    @nextcloud_method
    def get_group_folders(self):
        """
        Return a list of call configured folders and their settings

        Returns:

        """
        return self.requester.get()

    @nextcloud_method
    def get_group_folder(self, fid):
        """
        Return a specific configured folder and it's settings

        Args:
            fid (int/str): group folder id

        Returns:

        """
        return self.requester.get(fid)

    @nextcloud_method
    def create_group_folder(self, mountpoint):
        """
        Create a new group folder

        Args:
            mountpoint (str): name for the new folder

        Returns:

        """
        return self.requester.post(data={"mountpoint": mountpoint})

    @nextcloud_method
    def delete_group_folder(self, fid):
        """
        Delete a group folder

        Args:
            fid (int/str): group folder id

        Returns:

        """
        return self.requester.delete(fid)

    @nextcloud_method
    def grant_access_to_group_folder(self, fid, gid):
        """
        Give a group access to a folder

        Args:
            fid (int/str): group folder id
            gid (str): group to share with id

        Returns:

        """
        url = "/".join([str(fid), "groups"])
        return self.requester.post(url, data={"group": gid})

    @nextcloud_method
    def revoke_access_to_group_folder(self, fid, gid):
        """
        Remove access from a group to a folder

        Args:
            fid (int/str): group folder id
            gid (str): group id

        Returns:

        """
        url = "/".join([str(fid), "groups", gid])
        return self.requester.delete(url)

    @nextcloud_method
    def set_permissions_to_group_folder(self, fid, gid, permissions):
        """
        Set the permissions a group has in a folder

        Args:
            fid (int/str): group folder id
            gid (str): group id
            permissions (int): The new permissions for the group as attribute of Permission class

        Returns:

        """
        url = "/".join([str(fid), "groups", gid])
        return self.requester.post(url=url, data={"permissions": permissions})

    @nextcloud_method
    def set_quota_of_group_folder(self, fid, quota):
        """
        Set the quota for a folder in bytes

        Args:
            fid (int/str): group folder id
            quota (int/str): The new quota for the folder in bytes, user -3 for unlimited

        Returns:

        """
        url = "/".join([str(fid), "quota"])
        return self.requester.post(url, {"quota": quota})

    @nextcloud_method
    def rename_group_folder(self, fid, mountpoint):
        """
        Change the name of a folder

        Args:
            fid (int/str): group folder id
            mountpoint (str): The new name for the folder

        Returns:

        """
        url = "/".join([str(fid), "mountpoint"])
        return self.requester.post(url=url, data={"mountpoint": mountpoint})


class Share(WithRequester):
    API_URL = "/ocs/v2.php/apps/files_sharing/api/v1"
    LOCAL = "shares"

    def get_local_url(self, additional_url=""):
        if additional_url:
            return "/".join([self.LOCAL, additional_url])
        return self.LOCAL

    @staticmethod
    def validate_share_parameters(path, share_type, share_with):
        """
        Check if share parameters make sense

        Args:
            path (str): path to the file/folder which should be shared
            share_type (int): ShareType attribute
            share_with (str): user/group id with which the file should be shared

        Returns:
            bool: True if parameters make sense together, False otherwise
        """
        if (path is None or not isinstance(share_type, int)) \
                or (share_type in [ShareType.GROUP, ShareType.USER, ShareType.FEDERATED_CLOUD_SHARE]
                    and share_with is None):
            return False
        return True

    @nextcloud_method
    def get_shares(self):
        """ Get all shares from the user """
        return self.requester.get(self.get_local_url())

    @nextcloud_method
    def get_shares_from_path(self, path, reshares=None, subfiles=None):
        """
        Get all shares from a given file/folder

        Args:
            path (str): path to file/folder
            reshares (bool): (optional) return not only the shares from the current user but all shares from the given file
            subfiles (bool): (optional) return all shares within a folder, given that path defines a folder

        Returns:

        """
        url = self.get_local_url()
        params = {
            "path": path,
            "reshares": None if reshares is None else str(bool(reshares)).lower(),  # TODO: test reshares, subfiles
            "subfiles": None if subfiles is None else str(bool(subfiles)).lower(),
        }
        return self.requester.get(url, params=params)

    @nextcloud_method
    def get_share_info(self, sid):
        """
        Get information about a given share

        Args:
            sid (int): share id

        Returns:
        """
        return self.requester.get(self.get_local_url(sid))

    @nextcloud_method
    def create_share(
            self, path, share_type, share_with=None, public_upload=None,
            password=None, permissions=None):
        """
        Share a file/folder with a user/group or as public link

        Mandatory fields: share_type, path and share_with for share_type USER (0) or GROUP (1).

        Args:
            path (str): path to the file/folder which should be shared
            share_type (int): ShareType attribute
            share_with (str): user/group id with which the file should be shared
            public_upload (bool): bool, allow public upload to a public shared folder (true/false)
            password (str): password to protect public link Share with
            permissions (int): sum of selected Permission attributes

        Returns:

        """
        if not self.validate_share_parameters(path, share_type, share_with):
            return False

        url = self.get_local_url()
        if public_upload:
            public_upload = "true"

        data = {"path": path, "shareType": share_type}
        if share_type in [ShareType.GROUP, ShareType.USER, ShareType.FEDERATED_CLOUD_SHARE]:
            data["shareWith"] = share_with
        if public_upload:
            data["publicUpload"] = public_upload
        if share_type == ShareType.PUBLIC_LINK and password is not None:
            data["password"] = str(password)
        if permissions is not None:
            data["permissions"] = permissions
        return self.requester.post(url, data)

    @nextcloud_method
    def delete_share(self, sid):
        """
        Remove the given share

        Args:
            sid (str): share id

        Returns:

        """
        return self.requester.delete(self.get_local_url(sid))

    @nextcloud_method
    def update_share(self, sid, permissions=None, password=None, public_upload=None, expire_date=""):
        """
        Update a given share, only one value can be updated per request

        Args:
            sid (str): share id
            permissions (int): sum of selected Permission attributes
            password (str): password to protect public link Share with
            public_upload (bool): bool, allow public upload to a public shared folder (true/false)
            expire_date (str): set an expire date for public link shares. Format: ‘YYYY-MM-DD’

        Returns:

        """
        params = dict(
            permissions=permissions,
            password=password,
            expireDate=expire_date
        )
        if public_upload:
            params["publicUpload"] = "true"
        if public_upload is False:
            params["publicUpload"] = "false"

        # check if only one param specified
        specified_params_count = sum([int(bool(each)) for each in params.values()])
        if specified_params_count > 1:
            raise ValueError("Only one parameter for update can be specified per request")

        url = self.get_local_url(sid)
        return self.requester.put(url, data=params)


class FederatedCloudShare(WithRequester):
    API_URL = "/ocs/v2.php/apps/files_sharing/api/v1"
    FEDERATED = "remote_shares"

    def get_federated_url(self, additional_url=""):
        if additional_url:
            return "/".join([self.FEDERATED, additional_url])
        return self.FEDERATED

    @nextcloud_method
    def list_accepted_federated_cloudshares(self):
        url = self.get_federated_url()
        return self.requester.get(url)

    @nextcloud_method
    def get_known_federated_cloudshare(self, sid):
        url = self.get_federated_url(sid)
        return self.requester.get(url)

    @nextcloud_method
    def delete_accepted_federated_cloudshare(self, sid):
        url = self.get_federated_url(sid)
        return self.requester.delete(url)

    @nextcloud_method
    def list_pending_federated_cloudshares(self, sid):
        url = self.get_federated_url("pending")
        return self.requester.get(url)

    @nextcloud_method
    def accept_pending_federated_cloudshare(self, sid):
        url = self.get_federated_url("pending/{sid}".format(sid=sid))
        return self.requester.post(url)

    @nextcloud_method
    def decline_pending_federated_cloudshare(self, sid):
        url = self.get_federated_url("pending/{sid}".format(sid=sid))
        return self.requester.delete(url)


class Apps(WithRequester):
    API_URL = "/ocs/v1.php/cloud/apps"

    @nextcloud_method
    def get_apps(self, filter=None):
        """
        Get a list of apps installed on the Nextcloud server

        :param filter: str, optional "enabled" or "disabled"
        :return:
        """
        params = {
            "filter": filter
        }
        return self.requester.get(params=params)

    @nextcloud_method
    def get_app(self, app_id):
        """
        Provide information on a specific application

        :param app_id: str, app id
        :return:
        """
        return self.requester.get(app_id)

    @nextcloud_method
    def enable_app(self, app_id):
        """
        Enable an app

        :param app_id: str, app id
        :return:
        """
        return self.requester.post(app_id)

    @nextcloud_method
    def disable_app(self, app_id):
        """
        Disable the specified app

        :param app_id: str, app id
        :return:
        """
        return self.requester.delete(app_id)


class Group(WithRequester):
    API_URL = "/ocs/v1.php/cloud/groups"

    @nextcloud_method
    def get_groups(self, search=None, limit=None, offset=None):
        """
        Retrieve a list of groups from the Nextcloud server

        :param search: string, optional search string
        :param limit: int, optional limit value
        :param offset: int, optional offset value
        :return:
        """
        params = {
            'search': search,
            'limit': limit,
            'offset': offset
        }
        return self.requester.get(params=params)

    @nextcloud_method
    def add_group(self, gid):
        """
        Add a new group

        :param gid: str, group name
        :return:
        """
        msg = {"groupid": gid}
        return self.requester.post("", msg)

    @nextcloud_method
    def get_group(self, gid):
        """
        Retrieve a list of group members

        :param gid: str, group name
        :return:
        """
        return self.requester.get("{gid}".format(gid=gid))

    @nextcloud_method
    def get_subadmins(self, gid):
        """
        List subadmins of the group

        :param gid: str, group name
        :return:
        """
        return self.requester.get("{gid}/subadmins".format(gid=gid))

    @nextcloud_method
    def delete_group(self, gid):
        """
        Remove a group

        :param gid: str, group name
        :return:
        """
        return self.requester.delete("{gid}".format(gid=gid))


class User(WithRequester):
    API_URL = "/ocs/v1.php/cloud/users"

    @nextcloud_method
    def add_user(self, uid, passwd):
        """
        Create a new user on the Nextcloud server

        :param uid: str, uid of new user
        :param passwd: str, password of new user
        :return:
        """
        msg = {'userid': uid, 'password': passwd}
        return self.requester.post("", msg)

    @nextcloud_method
    def get_users(self, search=None, limit=None, offset=None):
        """
        Retrieve a list of users from the Nextcloud server

        :param search: string, optional search string
        :param limit: int, optional limit value
        :param offset: int, optional offset value
        :return:
        """
        params = {
            'search': search,
            'limit': limit,
            'offset': offset
        }
        return self.requester.get(params=params)

    @nextcloud_method
    def get_user(self, uid):
        """
        Retrieve information about a single user

        :param uid: str, uid of user
        :return:
        """
        return self.requester.get("{uid}".format(uid=uid))

    @nextcloud_method
    def edit_user(self, uid, what, value):
        """
        Edit attributes related to a user

        Users are able to edit email, displayname and password; admins can also edit the quota value

        :param uid: str, uid of user
        :param what: str, the field to edit
        :param value: str, the new value for the field
        :return:
        """
        what_to_key_map = dict(
            email="email", quota="quote", phone="phone", address="address", website="website",
            twitter="twitter", displayname="displayname", password="password",
        )
        assert what in what_to_key_map, (
            "You have chosen to edit user's '{what}', but you can choose only from: {choices}"
            .format(what=what, choices=", ".join(what_to_key_map.keys()))
        )

        url = "{uid}".format(uid=uid)
        msg = dict(
            key=what_to_key_map[what],
            value=value,
        )
        return self.requester.put(url, msg)

    @nextcloud_method
    def disable_user(self, uid):
        """
        Disable a user on the Nextcloud server so that the user cannot login anymore

        :param uid: str, uid of user
        :return:
        """
        return self.requester.put("{uid}/disable".format(uid=uid))

    @nextcloud_method
    def enable_user(self, uid):
        """
        Enable a user on the Nextcloud server so that the user can login again

        :param uid: str, uid of user
        :return:
        """
        return self.requester.put("{uid}/enable".format(uid=uid))

    @nextcloud_method
    def delete_user(self, uid):
        """
        Delete a user from the Nextcloud server

        :param uid: str, uid of user
        :return:
        """
        return self.requester.delete("{uid}".format(uid=uid))

    @nextcloud_method
    def add_to_group(self, uid, gid):
        """
        Add the specified user to the specified group

        :param uid: str, uid of user
        :param gid: str, name of group
        :return:
        """
        url = "{uid}/groups".format(uid=uid)
        msg = {'groupid': gid}
        return self.requester.post(url, msg)

    @nextcloud_method
    def remove_from_group(self, uid, gid):
        """
        Remove the specified user from the specified group

        :param uid: str, uid of user
        :param gid: str, name of group
        :return:
        """
        url = "{uid}/groups".format(uid=uid)
        msg = {'groupid': gid}
        return self.requester.delete(url, msg)

    @nextcloud_method
    def create_subadmin(self, uid, gid):
        """
        Make a user the subadmin of a group

        :param uid: str, uid of user
        :param gid: str, name of group
        :return:
        """
        url = "{uid}/subadmins".format(uid=uid)
        msg = {'groupid': gid}
        return self.requester.post(url, msg)

    @nextcloud_method
    def remove_subadmin(self, uid, gid):
        """
        Remove the subadmin rights for the user specified from the group specified

        :param uid: str, uid of user
        :param gid: str, name of group
        :return:
        """
        url = "{uid}/subadmins".format(uid=uid)
        msg = {'groupid': gid}
        return self.requester.delete(url, msg)

    @nextcloud_method
    def get_subadmin_groups(self, uid):
        """
        Get the groups in which the user is a subadmin

        :param uid: str, uid of user
        :return:
        """
        url = "{uid}/subadmins".format(uid=uid)
        return self.requester.get(url)

    @nextcloud_method
    def resend_welcome_mail(self, uid):
        """
        Trigger the welcome email for this user again

        :param uid: str, uid of user
        :return:
        """
        url = "{uid}/welcome".format(uid=uid)
        return self.requester.post(url)


class Activity(WithRequester):
    API_URL = "/ocs/v2.php/apps/activity/api/v2/activity"

    @nextcloud_method
    def get_activities(self, since=None, limit=None, object_type=None, object_id=None, sort=None):
        """
        Get an activity feed showing your file changes and other interesting things going on in your Nextcloud

        All args are optional

        Args:
            since (int): ID of the last activity that you’ve seen
            limit (int): How many activities should be returned (default: 50)
            object_type (string): Filter the activities to a given object. May only appear together with object_id
            object_id (string): Filter the activities to a given object. May only appear together with object_type
            sort (str, "asc" or "desc"): Sort activities ascending or descending (from the since) (Default: desc)

        Returns:

        """
        params = dict(
            since=since,
            limit=limit,
            object_type=object_type,
            object_id=object_id,
            sort=sort
        )
        if params['object_type'] and params['object_id']:
            return self.requester.get(url="filter", params=params)
        return self.requester.get(params=params)


class Notifications(WithRequester):
    API_URL = "/ocs/v2.php/apps/notifications/api/v2/notifications"

    @nextcloud_method
    def get_notifications(self):
        """ Get list of notifications for a logged in user """
        return self.requester.get()

    @nextcloud_method
    def get_notification(self, notification_id):
        """
        Get single notification by id for a user

        Args:
            notification_id (int): Notification id

        Returns:

        """
        return self.requester.get(url=notification_id)

    @nextcloud_method
    def delete_notification(self, notification_id):
        """
        Delete single notification by id for a user

        Args:
            notification_id (int): Notification id

        Returns:

        """
        return self.requester.delete(url=notification_id)

    @nextcloud_method
    def delete_all_notifications(self):
        """ Delete all notification for a logged in user

        Notes:
            This endpoint was added for Nextcloud 14
        """
        return self.requester.delete()


class UserLDAP(WithRequester):
    API_URL = "/ocs/v2.php/apps/user_ldap/api/v1/config"

    # (name_stem, argname, docstring)
    CONFIG_KEYS = [
        "ldapHost",
        "ldapPort",
        "ldapBackupHost",
        "ldapBackupPort",
        "ldapBase",
        "ldapBaseUsers",
        "ldapBaseGroups",
        "ldapAgentName",
        "ldapAgentPassword",
        "ldapTLS",
        "turnOffCertCheck",
        "ldapUserDisplayName",
        "ldapGidNumber",
        "ldapUserFilterObjectclass",
        "ldapUserFilterGroups",
        "ldapUserFilter",
        "ldapUserFilterMode",
        "ldapGroupFilter",
        "ldapGroupFilterMode",
        "ldapGroupFilterObjectclass",
        "ldapGroupFilterGroups",
        "ldapGroupMemberAssocAttr",
        "ldapGroupDisplayName",
        "ldapLoginFilter",
        "ldapLoginFilterMode",
        "ldapLoginFilterEmail",
        "ldapLoginFilterUsername",
        "ldapLoginFilterAttributes",
        "ldapQuotaAttribute",
        "ldapQuotaDefault",
        "ldapEmailAttribute",
        "ldapCacheTTL",
        "ldapUuidUserAttribute",
        "ldapUuidGroupAttribute",
        "ldapOverrideMainServer",
        "ldapConfigurationActive",
        "ldapAttributesForUserSearch",
        "ldapAttributesForGroupSearch",
        "ldapExperiencedAdmin",
        "homeFolderNamingRule",
        "hasPagedResultSupport",
        "hasMemberOfFilterSupport",
        "useMemberOfToDetectMembership",
        "ldapExpertUsernameAttr",
        "ldapExpertUUIDUserAttr",
        "ldapExpertUUIDGroupAttr",
        "lastJpegPhotoLookup",
        "ldapNestedGroups",
        "ldapPagingSize",
        "turnOnPasswordChange",
        "ldapDynamicGroupMemberURL",
        "ldapDefaultPPolicyDN",
    ]

    def __init__(self, *args, **kwargs):
        super(UserLDAP, self).__init__(*args, **kwargs)
        for key in self.CONFIG_KEYS:
            key_name = re.sub('ldap', '', key)
            key_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', key_name).lower()

            # create and add getter method
            getter_name = "get_ldap_{}".format(key_name)
            exec(
                """def {}(self, config_id):
                    res = self.get_ldap_config(config_id)
                    data = res['ocs']['data']
                    return data["{}"]
                """.format(getter_name, key)
            )
            getter_function = locals()[getter_name]

            getter_method = types.MethodType(getter_function, self)
            PUBLIC_API_NAME_CLASS_MAP[getter_name] = self.__class__.__name__
            setattr(self, getter_name, getter_method)

            # create and add setter method
            setter_name = "set_ldap_{}".format(key_name)
            exec(
                """def {0}(self, config_id, value):
                    res = self.edit_ldap_config(config_id, data={{"{1}": value}})
                    return res
                """.format(setter_name, key)
            )
            setter_function = locals()[setter_name]

            setter_method = types.MethodType(setter_function, self)
            PUBLIC_API_NAME_CLASS_MAP[setter_name] = self.__class__.__name__
            setattr(self, setter_name, setter_method)

    @nextcloud_method
    def create_ldap_config(self):
        """ Create a new and empty LDAP configuration """
        return self.requester.post()

    @nextcloud_method
    def get_ldap_config(self, config_id, show_password=None):
        """
        Get all keys and values of the specified LDAP configuration

        Args:
            config_id (str): User LDAP config id
            show_password (int): 0 or 1 whether to return the password in clear text (default 0)

        Returns:

        """
        params = dict(showPassword=show_password)
        return self.requester.get(config_id, params=params)

    @nextcloud_method
    def edit_ldap_config(self, config_id, data):
        """
        Update a configuration with the provided values

        You can find list of all config keys in get_ldap_config method response or in Nextcloud docs

        Args:
            config_id (str): User LDAP config id
            data (dict): config values to update

        Returns:

        """
        # TODO: refactor to provide methods for configuration s.a. edit_ldap_password and get_ldap_password
        prepared_data = {'configData[{}]'.format(key): value for key, value in data.items()}
        return self.requester.put(config_id, data=prepared_data)

    @nextcloud_method
    def delete_ldap_config(self, config_id):
        """
        Delete a given LDAP configuration

        Args:
            config_id (str): User LDAP config id

        Returns:

        """
        return self.requester.delete(config_id)


class OCSCode(enum.IntEnum):
    OK = 100
    SERVER_ERROR = 996
    NOT_AUTHORIZED = 997
    NOT_FOUND = 998
    UNKNOWN_ERROR = 999


class ShareType(enum.IntEnum):
    USER = 0
    GROUP = 1
    PUBLIC_LINK = 3
    FEDERATED_CLOUD_SHARE = 6


class Permission(enum.IntEnum):
    """ Permission for Share have to be sum of selected permissions """
    READ = 1
    UPDATE = 2
    CREATE = 4
    DELETE = 8
    SHARE = 16
    ALL = 31


QUOTA_UNLIMITED = -3


def datetime_to_expire_date(date):
    return date.strftime("%Y-%m-%d")
