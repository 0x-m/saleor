import pytest

import graphene
from tests.api.utils import assert_read_only_mode


CREATE_FULFILLMENT_QUERY = """
    mutation fulfillOrder(
        $order: ID, $lines: [FulfillmentLineInput]!, $tracking: String,
        $notify: Boolean
    ) {
        orderFulfillmentCreate(
            order: $order,
            input: {
                lines: $lines, trackingNumber: $tracking,
                notifyCustomer: $notify}
        ) {
            errors {
                field
                message
            }
            fulfillment {
                fulfillmentOrder
                status
                trackingNumber
            lines {
                totalCount
            }
        }
    }
}
"""


def test_create_fulfillment(
        staff_api_client, order_with_lines, staff_user,
        permission_manage_orders):
    order = order_with_lines
    query = CREATE_FULFILLMENT_QUERY
    order_id = graphene.Node.to_global_id('Order', order.id)
    order_line = order.lines.first()
    order_line_id = graphene.Node.to_global_id('OrderLine', order_line.id)
    tracking = 'Flames tracking'
    assert not order.events.all()
    variables = {
        'order': order_id,
        'lines': [{'orderLineId': order_line_id, 'quantity': 1}],
        'tracking': tracking, 'notify': True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


@pytest.mark.parametrize(
    'quantity, error_message',
    (
        (0, 'Quantity must be larger than 0.'),
        (100, 'Only 3 items remaining to fulfill.')))
def test_create_fulfillment_not_sufficient_quantity(
        staff_api_client, order_with_lines, staff_user, quantity,
        error_message, permission_manage_orders):
    query = CREATE_FULFILLMENT_QUERY
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id('OrderLine', order_line.id)
    variables = {
        'order': graphene.Node.to_global_id('Order', order_with_lines.id),
        'lines': [{'orderLineId': order_line_id, 'quantity': quantity}]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_fulfillment_update_tracking(
        staff_api_client, fulfillment, permission_manage_orders):
    query = """
    mutation updateFulfillment($id: ID!, $tracking: String) {
            orderFulfillmentUpdateTracking(
                id: $id, input: {trackingNumber: $tracking}) {
                    fulfillment {
                        trackingNumber
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    tracking = 'stationary tracking'
    variables = {'id': fulfillment_id, 'tracking': tracking}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_cancel_fulfillment_restock_items(
        staff_api_client, fulfillment, staff_user, permission_manage_orders):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            orderFulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    variables = {'id': fulfillment_id, 'restock': True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)


def test_cancel_fulfillment(
        staff_api_client, fulfillment, staff_user, permission_manage_orders):
    query = """
    mutation cancelFulfillment($id: ID!, $restock: Boolean) {
            orderFulfillmentCancel(id: $id, input: {restock: $restock}) {
                    fulfillment {
                        status
                    }
                }
        }
    """
    fulfillment_id = graphene.Node.to_global_id('Fulfillment', fulfillment.id)
    variables = {'id': fulfillment_id, 'restock': False}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    assert_read_only_mode(response)
