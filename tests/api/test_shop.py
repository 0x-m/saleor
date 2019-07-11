import graphene
from django_countries import countries

from saleor.core.permissions import MODELS_PERMISSIONS
from saleor.graphql.core.utils import str_to_enum
from saleor.site import AuthenticationBackends
from saleor.site.models import Site
from tests.api.utils import assert_read_only_mode, get_graphql_content

from .utils import assert_read_only_mode


def test_query_authorization_keys(
    authorization_key, staff_api_client, permission_manage_settings
):
    query = """
    query {
        shop {
            authorizationKeys {
                name
                key
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["authorizationKeys"][0]["name"] == "FACEBOOK"
    assert data["authorizationKeys"][0]["key"] == authorization_key.key


def test_query_countries(user_api_client):
    query = """
    query {
        shop {
            countries {
                code
                country
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["countries"]) == len(countries)


def test_query_currencies(user_api_client, settings):
    query = """
    query {
        shop {
            currencies
            defaultCurrency
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["currencies"]) == len(settings.AVAILABLE_CURRENCIES)
    assert data["defaultCurrency"] == settings.DEFAULT_CURRENCY


def test_query_name(user_api_client, site_settings):
    query = """
    query {
        shop {
            name
            description
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["description"] == site_settings.description
    assert data["name"] == site_settings.site.name


def test_query_company_address(user_api_client, site_settings, address):
    query = """
    query {
        shop{
            companyAddress{
                city
                streetAddress1
                postalCode
            }
        }
    }
    """
    site_settings.company_address = address
    site_settings.save()
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    company_address = data["companyAddress"]
    assert company_address["city"] == address.city
    assert company_address["streetAddress1"] == address.street_address_1
    assert company_address["postalCode"] == address.postal_code


def test_query_domain(user_api_client, site_settings, settings):
    query = """
    query {
        shop {
            domain {
                host
                sslEnabled
                url
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["domain"]["host"] == site_settings.site.domain
    assert data["domain"]["sslEnabled"] == settings.ENABLE_SSL
    assert data["domain"]["url"]


def test_query_languages(settings, user_api_client):
    query = """
    query {
        shop {
            languages {
                code
                language
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["languages"]) == len(settings.LANGUAGES)


def test_query_permissions(staff_api_client, permission_manage_users):
    query = """
    query {
        shop {
            permissions {
                code
                name
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    permissions = data["permissions"]
    permissions_codes = {permission.get("code") for permission in permissions}
    assert len(permissions_codes) == len(MODELS_PERMISSIONS)
    for code in permissions_codes:
        assert code in [str_to_enum(code.split(".")[1]) for code in MODELS_PERMISSIONS]


def test_query_navigation(user_api_client, site_settings):
    query = """
    query {
        shop {
            navigation {
                main {
                    name
                }
                secondary {
                    name
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    navigation_data = content["data"]["shop"]["navigation"]
    assert navigation_data["main"]["name"] == site_settings.top_menu.name
    assert navigation_data["secondary"]["name"] == site_settings.bottom_menu.name


def test_query_charge_taxes_on_shipping(api_client, site_settings):
    query = """
    query {
        shop {
            chargeTaxesOnShipping
        }
    }"""
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    charge_taxes_on_shipping = site_settings.charge_taxes_on_shipping
    assert data["chargeTaxesOnShipping"] == charge_taxes_on_shipping


def test_query_digital_content_settings(
    staff_api_client, site_settings, permission_manage_settings
):
    query = """
    query {
        shop {
            automaticFulfillmentDigitalProducts
            defaultDigitalMaxDownloads
            defaultDigitalUrlValidDays
        }
    }"""

    max_download = 2
    url_valid_days = 3
    site_settings.automatic_fulfillment_digital_products = True
    site_settings.default_digital_max_downloads = max_download
    site_settings.default_digital_url_valid_days = url_valid_days
    site_settings.save()

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    automatic_fulfillment = site_settings.automatic_fulfillment_digital_products
    assert data["automaticFulfillmentDigitalProducts"] == automatic_fulfillment
    assert data["defaultDigitalMaxDownloads"] == max_download
    assert data["defaultDigitalUrlValidDays"] == url_valid_days


def test_shop_digital_content_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    query = """
        mutation updateSettings($input: ShopSettingsInput!) {
            shopSettingsUpdate(input: $input) {
                shop {
                    automaticFulfillmentDigitalProducts
                    defaultDigitalMaxDownloads
                    defaultDigitalUrlValidDays
                }
                errors {
                    field,
                    message
                }
            }
        }
    """

    max_downloads = 15
    url_valid_days = 30
    variables = {
        "input": {
            "automaticFulfillmentDigitalProducts": True,
            "defaultDigitalMaxDownloads": max_downloads,
            "defaultDigitalUrlValidDays": url_valid_days,
        }
    }

    assert not site_settings.automatic_fulfillment_digital_products
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_shop_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    query = """
        mutation updateSettings($input: ShopSettingsInput!) {
            shopSettingsUpdate(input: $input) {
                shop {
                    headerText,
                    includeTaxesInPrices,
                    chargeTaxesOnShipping
                }
                errors {
                    field,
                    message
                }
            }
        }
    """
    variables = {"input": {"includeTaxesInPrices": False, "headerText": "Lorem ipsum"}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_shop_domain_update(staff_api_client, permission_manage_settings):
    query = """
        mutation updateSettings($input: SiteDomainInput!) {
            shopDomainUpdate(input: $input) {
                shop {
                    name
                    domain {
                        host,
                    }
                }
            }
        }
    """
    new_name = "saleor test store"
    variables = {"input": {"domain": "lorem-ipsum.com", "name": new_name}}
    site = Site.objects.get_current()
    assert site.domain != "lorem-ipsum.com"
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_homepage_collection_update(
    staff_api_client, collection, permission_manage_settings
):
    query = """
        mutation homepageCollectionUpdate($collection: ID!) {
            homepageCollectionUpdate(collection: $collection) {
                shop {
                    homepageCollection {
                        id,
                        name
                    }
                }
            }
        }
    """
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"collection": collection_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_homepage_collection_update_set_null(
    staff_api_client, collection, site_settings, permission_manage_settings
):
    query = """
        mutation homepageCollectionUpdate($collection: ID) {
            homepageCollectionUpdate(collection: $collection) {
                shop {
                    homepageCollection {
                        id
                    }
                }
            }
        }
    """
    site_settings.homepage_collection = collection
    site_settings.save()
    variables = {"collection": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_query_default_country(user_api_client, settings):
    settings.DEFAULT_COUNTRY = "US"
    query = """
    query {
        shop {
            defaultCountry {
                code
                country
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["defaultCountry"]
    assert data["code"] == settings.DEFAULT_COUNTRY
    assert data["country"] == "United States of America"


def test_query_geolocalization(user_api_client):
    query = """
        query {
            shop {
                geolocalization {
                    country {
                        code
                    }
                }
            }
        }
    """
    GERMAN_IP = "79.222.222.22"
    response = user_api_client.post_graphql(query, HTTP_X_FORWARDED_FOR=GERMAN_IP)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["geolocalization"]
    assert data["country"]["code"] == "DE"

    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["geolocalization"]
    assert data["country"] is None


AUTHORIZATION_KEY_ADD = """
mutation AddKey($key: String!, $password: String!, $keyType: AuthorizationKeyType!) {
    authorizationKeyAdd(input: {key: $key, password: $password}, keyType: $keyType) {
        errors {
            field
            message
        }
        authorizationKey {
            name
            key
        }
    }
}
"""


def test_mutation_authorization_key_add_existing(
    staff_api_client, authorization_key, permission_manage_settings
):

    # adding a key of type that already exists should return an error
    assert authorization_key.name == AuthenticationBackends.FACEBOOK
    variables = {"keyType": "FACEBOOK", "key": "key", "password": "secret"}
    response = staff_api_client.post_graphql(
        AUTHORIZATION_KEY_ADD, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_mutation_authorization_key_add(staff_api_client, permission_manage_settings):

    # mutation with correct input data should create a new key instance
    variables = {"keyType": "FACEBOOK", "key": "key", "password": "secret"}
    response = staff_api_client.post_graphql(
        AUTHORIZATION_KEY_ADD, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_mutation_authorization_key_delete(
    staff_api_client, authorization_key, permission_manage_settings
):

    query = """
    mutation DeleteKey($keyType: AuthorizationKeyType!) {
        authorizationKeyDelete(keyType: $keyType) {
            errors {
                field
                message
            }
            authorizationKey {
                name
                key
            }
        }
    }
    """

    assert authorization_key.name == AuthenticationBackends.FACEBOOK

    # deleting non-existing key should return an error
    variables = {"keyType": "FACEBOOK"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)


def test_mutation_update_company_address(
    staff_api_client,
    authorization_key,
    permission_manage_settings,
    address,
    site_settings,
):
    query = """
    mutation updateShopAddress($input: AddressInput!){
        shopAddressUpdate(input: $input){
            errors{
                field
                message
            }
        }
    }
    """
    variables = {
        "input": {
            "streetAddress1": address.street_address_1,
            "city": address.city,
            "country": address.country.code,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    assert_read_only_mode(response)
