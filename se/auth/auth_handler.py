# coding=utf-8

#
# Copyright 2013 nava
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from se import config

class BaseAuthHanlder(object):
    def authenticate_redirect(self, callback_uri=None,
                              ax_attrs=["name", "email", "language", "username"]):
        """Returns the authentication URL for this service.

        After authentication, the service will redirect back to the given
        callback URI.

        We request the given attributes for the authenticated user by
        default (name, email, language, and username). If you don't need
        all those attributes for your app, you can request fewer with
        the ax_attrs keyword argument.
        """
        pass

    def get_authenticated_user(self, callback, http_client=None):
        """Fetches the authenticated user data upon redirect.

        This method should be called by the handler that receives the
        redirect from the authenticate_redirect() or authorize_redirect()
        methods.
        """
        # Verify the OpenID response via direct request to the OP
        pass


class TrustIPAuth(BaseAuthHanlder):

    def get_authenticated_user(self, remote_ip, trust_ip_list, callback):
        """Fetches the authenticated user data upon redirect.

        This method should be called by the handler that receives the
        redirect from the authenticate_redirect() or authorize_redirect()
        methods.
        """
        can_read = False
        for ip_address in trust_ip_list:
            if ip_address == remote_ip:
                can_read = True
                break
            elif "*" in ip_address:
                ip_address = ip_address.replace("*","")
                if ip_address in remote_ip:
                    can_read = True
                    break

        user = dict()
        user['can_read'] = can_read
        callback(user)