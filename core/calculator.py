def calculate_order_total(order):

    total = 0

    for item in order["items"]:
        total += item["revenue"]

    return total


def calculate_profit(order, product_cost_map):

    profit = 0

    for item in order["items"]:
        cost = product_cost_map.get(item["sku"], 0)
        revenue = item["revenue"]

        profit += (revenue - (cost * item["qty"]))

    return profit
