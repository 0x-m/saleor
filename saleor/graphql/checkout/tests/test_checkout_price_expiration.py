from datetime import timedelta
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from saleor.graphql.checkout.mutations import invalidate_checkout_prices
from saleor.graphql.tests.utils import get_graphql_content


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_add_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    # given
    query = """
mutation addCheckoutLine($checkoutId: ID!, $line: CheckoutLineInput!){
  checkoutLinesAdd(checkoutId: $checkoutId, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "checkoutId": graphene.Node.to_global_id("Checkout", checkout_with_items.pk),
        "line": {
            "quantity": 1,
            "variantId": graphene.Node.to_global_id(
                "ProductVariant", stock.product_variant.pk
            ),
        },
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLinesAdd"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    stock,
):
    # given
    query = """
mutation updateCheckoutLine($token: UUID, $line: CheckoutLineInput!){
  checkoutLinesUpdate(token: $token, lines: [$line]) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "line": {
            "quantity": 1,
            "variantId": graphene.Node.to_global_id(
                "ProductVariant", stock.product_variant.pk
            ),
        },
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLinesUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_lines_delete_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
):
    # given
    query = """
mutation updateCheckoutLine($token: UUID, $lineId: ID){
  checkoutLineDelete(token: $token, lineId: $lineId) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "lineId": graphene.Node.to_global_id(
            "CheckoutLine", checkout_with_items.lines.first().pk
        ),
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutLineDelete"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_shipping_address_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    graphql_address_data,
):
    # given
    query = """
mutation UpdateCheckoutShippingAddress($token: UUID, $address: AddressInput!) {
  checkoutShippingAddressUpdate(token: $token, shippingAddress: $address) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "address": graphql_address_data,
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutShippingAddressUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@patch("saleor.graphql.checkout.mutations.invalidate_checkout_prices")
def test_checkout_billing_address_update_invalidate_prices(
    mocked_function,
    api_client,
    checkout_with_items,
    graphql_address_data,
):
    # given
    query = """
mutation UpdateCheckoutBillingAddress($token: UUID, $address: AddressInput!) {
  checkoutBillingAddressUpdate(token: $token, billingAddress: $address) {
    errors {
      field
      message
    }
  }
}
"""
    variables = {
        "token": checkout_with_items.token,
        "address": graphql_address_data,
    }

    # when
    response = get_graphql_content(api_client.post_graphql(query, variables))

    # then
    assert not response["data"]["checkoutBillingAddressUpdate"]["errors"]
    mocked_function.assert_called_once_with(checkout_with_items)


@freeze_time("2020-12-12 12:00:00")
def test_invalidate_checkout_prices(checkout):
    # given
    checkout.price_expiration += timedelta(minutes=5)
    checkout.save(update_fields=["price_expiration"])

    # when
    invalidate_checkout_prices(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.price_expiration == timezone.now()
