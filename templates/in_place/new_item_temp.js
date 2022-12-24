{% load dash_utils %}


const $eatinsElem = $("#eatinsTable"),
      $modalsElem = $("#dynModals"),
      $deliveriesElem = $("#deliveriesTable"),
      eatinsElemTemp = `
        {% if restaurant.restaurant_orders|qs_exists:"eatins" %}
            {% for order in restaurant.restaurant_orders|reverse_manager_using:"eatins" %}
                <tr id="order-tr-{{ order.public_uuid }}">
                    <td>
                        <div class="form-check">
                            <label class="form-check-label">
                                <input 
                                       id="{{ order.public_uuid }}-done"
                                       class="form-check-input" 
                                       type="checkbox"
                                       {% if order.done %}checked{% endif %}
                                      >
                                    <span class="form-check-sign">
                                        <span class="check"></span>
                                    </span>
                                </label>
                            </div>
                        </td>
                        <td>
                            {{ order.timestamp|date:"h:i A" }} 
                            - order {{ order.order_number }}
                            , table {{ order.order_dinein.table_number }}
                        </td>
                        <td class="td-actions text-right">
                            <button 
                                    type="button" 
                                    rel="tooltip" 
                                    title="Edit Order"
                                    class="btn btn-white btn-link btn-sm"
                                    data-toggle="modal"
                                    data-target="#edit-order-{{ order.public_uuid }}"
                                >
                                <i class="material-icons">edit</i>
                            </button>
                            {% if user.user_staff.can_delete_orders %}
                                <button 
                                        type="button" 
                                        rel="tooltip" 
                                        title="Delete Order"
                                        class="btn btn-white btn-link btn-sm" 
                                        data-toggle="modal" 
                                        data-target="#delete-order-{{ order.public_uuid }}"
                                    >
                                    <i class="material-icons">delete</i>
                                </button>
                            {% endif %}
                        </td>
                    </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td>
                        <h3 class="text-center">We've had no eatins today so far.</h4>
                    </td>
                </tr>
                <tr>
                    <td>
                        <h6 class="text-center">
                            <a href="{% url 'in_place:orders' %}">
                                take a look at all orders instead
                            </a>
                    </h6>
                </td>
            </tr>
        {% endif %}
        `,
          deliveriesElemTemp = `
          {% if restaurant.restaurant_orders|qs_exists:"deliveries" %}
                                        {% for order in restaurant.restaurant_orders|reverse_manager_using:"deliveries" %}
                                            <tr id="order-tr-{{ order.public_uuid }}">
                                                <td>
                                                    <div class="form-check">
                                                        <label class="form-check-label">
                                                            <input 
                                                                   class="form-check-input is-done" 
                                                                   type="checkbox"
                                                                   id="{{ order.public_uuid }}-done"
                                                                   {% if order.done %}checked{% endif %}
                                                                  >
                                                            <span class="form-check-sign">
                                                                <span class="check"></span>
                                                            </span>
                                                        </label>
                                                    </div>
                                                </td>
                                                <td>
                                                    {{ order.timestamp|date:"h:i A" }} 
                                                    - no. {{ order.order_number }}
                                                </td>
                                                <td class="td-actions text-right">
                                                    <button 
                                                            type="button" 
                                                            rel="tooltip" 
                                                            title="Edit Order"
                                                            class="btn btn-white btn-link btn-sm"
                                                            data-toggle="modal"
                                                            data-target="#edit-order-{{ order.public_uuid }}"
                                                        >
                                                        <i class="material-icons">edit</i>
                                                    </button>
                                                    {% if user.user_staff.can_delete_orders %}
                                                        <button 
                                                                type="button" 
                                                                rel="tooltip" 
                                                                title="Delete Order"
                                                                class="btn btn-white btn-link btn-sm" 
                                                                data-toggle="modal" 
                                                                data-target="#delete-order-{{ order.public_uuid }}"
                                                            >
                                                            <i class="material-icons">delete</i>
                                                        </button>
                                                    {% endif %}
                                                </td>
                                            </tr>
                                        {% endfor %}
                                    {% else %}
                                        <tr>
                                            <td>
                                                <h3 class="text-center">We've had no deliveries today so far.</h4>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <h6 class="text-center">
                                                    <a href="{% url 'in_place:orders' %}">
                                                        take a look at all orders instead
                                                    </a>
                                                </h6>
                                            </td>
                                        </tr>
                                    {% endif %}
          `,
          editModalTemp = `
            {% for order in orders %}
                <div 
                     class="modal fade"
                     id="edit-order-{{ order.qs.public_uuid }}"
                     tabindex="-1"
                     role="dialog"
                    >
                    <div class="modal-dialog modal-lg" role="document">
                        <div class="modal-content bg-dark">
                            <div class="modal-header">
                                <h5 class="modal-title text-light">
                                    Edit Order
                                </h5>
                                <button 
                                        type="button" 
                                        class="close" 
                                        data-dismiss="modal" 
                                        aria-label="Close"
                                    >
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <form 
                                      method="POST" 
                                      action="{% url 'in_place:edit_order' %}"
                                      class="edit_form"
                                      id="editOrderForm-{{ order.qs.public_uuid }}"
                                    >
                                    <div class="csrfmidd"></div>
                                    {{ order.formset.management_form }}
                                    <input type="hidden" name="dest" value="dashboard">
                                    <div class="table-responsive">
                                        <table class="table table-dark table-bordered">
                                            <thead class="thead-dark">
                                                <tr>
                                                    <th>item</th>
                                                    <th>count</th>
                                                    <th>fee</th>
                                                    <th>auto price</th>
                                                    <th>total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for form in order.formset.forms %}
                                                    <tr>
                                                        <td 
                                                            rel="tooltip"
                                                            class="order-item-td"
                                                            style="width:30%"
                                                        >{{ form.item }}</td>
                                                        <td style="width:10%">{{ form.count }}</td>
                                                        <td>{{ form.fee }}</td>
                                                        <td style="width:8%">
                                                            <label
                                                                class="form-check-label d-flex justify-content-center 
                                                                        align-items-center align-content-center"
                                                                >
                                                                {{ form.auto_price }}
                                                                <span class="form-check-sign">
                                                                    <span class="check"></span>
                                                                </span>
                                                            </label>
                                                        </td>
                                                        <td>{{ form.paid_price }}</td>
                                                    </tr>
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                    </div>
                                    <div>
                                        <hr>
                                        <div class="mx-3 mt-4">
                                            {% for val, choice in order.order_form.order_type.field.choices %}
                                                <div class="form-check form-check-radio">
                                                    <label class="form-check-label">
                                                        <input 
                                                            type="radio" 
                                                            class="form-check-input" 
                                                            name="order_type" 
                                                            value="{{ val }}"
                                                            {% if val == order.order_form.order_type.value %}
                                                                checked
                                                            {% endif %}   
                                                            >
                                                        {{ choice|upper }}
                                                        <span class="circle">
                                                            <span class="check"></span>
                                                        </span>
                                                    </label>
                                                </div>
                                            {% endfor %}
                                            <input 
                                                type="hidden"
                                                name="public_uuid"
                                                value="{{ order.qs.public_uuid }}"
                                                >
                                        </div>
                                        <div class="dinein_info" id="dinein_info-{{order.qs.public_uuid}}">
                                            <hr>
                                            <div class="mt-5 mx-3">
                                                <div class="form-group">
                                                    <label for="dinein_table_num" class="bmd-label-floating">
                                                        {{ order.dinein_form.table_number.label|title }}*
                                                    </label>
                                                    {{ order.dinein_form.table_number }}
                                                    <span class="text-warning my-2">
                                                        {{ order.dinein_form.table_number.errors }}
                                                    </span>
                                                </div>
                                                <div class="form-group">
                                                    <label for="dinein_desc" class="bmd-label-floating">
                                                        {{ order.dinein_form.description.label|title }}
                                                    </label>
                                                    {{ order.dinein_form.description }}
                                                    <span class="text-warning my-2">
                                                        {{ order.dinein_form.description.errors }}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">
                                    Close
                                </button>
                                <button 
                                        type="button" 
                                        class="btn btn-primary" 
                                        onclick="javascript:$('#editOrderForm-{{ order.qs.public_uuid }}').submit()"
                                    >
                                    Edit
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            {% endfor %}
        `,
         deleteModalTemp = `
            {% if user.user_staff.can_delete_orders %}
                {% for order in orders %}
                    <div 
                         class="modal fade" 
                         id="delete-order-{{ order.qs.public_uuid }}" 
                         tabindex="-1" 
                         role="dialog" 
                        >
                        <div class="modal-dialog modal-lg" role="document">
                            <div class="modal-content bg-dark">
                                <div class="modal-header">
                                    <h5 class="modal-title text-light">
                                        Delete Order
                                    </h5>
                                    <button 
                                            type="button" 
                                            class="close" 
                                            data-dismiss="modal" 
                                            aria-label="Close"
                                        >
                                        <span aria-hidden="true">&times;</span>
                                    </button>
                                </div>
                                <div class="modal-body text-light">
                                    <h3 class="text-bolder">
                                        Are you sure you want to delete your record of this order?
                                    </h3>
                                    <form 
                                          method="POST" 
                                          action="{% url 'in_place:delete_order' %}"
                                          id="delete-order-form-{{ order.qs.public_uuid }}"
                                         >
                                        <div class="csrfmidd"></div>
                                        <input 
                                               type="hidden" 
                                               name="public_uuid" 
                                               value="{{ order.qs.public_uuid }}"
                                              >
                                        <input 
                                               type="hidden"
                                               name="dest"
                                               value="dashboard"
                                              >
                                    </form>
                                </div>
                                <div class="modal-footer">
                                    <button 
                                            type="button" 
                                            class="btn btn-secondary" 
                                            data-dismiss="modal"
                                        >
                                        Close
                                    </button>
                                    <button
                                    type="button" 
                                    class="btn btn-danger" 
                                    onclick="javascript:$('#delete-order-form-{{ order.qs.public_uuid }}').submit()"
                                    >
                                        Yes
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            {% endif %}
         `;

    $deliveriesElem.html(deliveriesElemTemp);
    $eatinsElem.html(eatinsElemTemp);
    $modalsElem.html(editModalTemp+deleteModalTemp);

    $.notify({
        icon: 'info',
        type: 'info',
        message: 'You have a new order.'
    });
    

    // Initializing variables for updating the charts
    const sale_chart_values = "{{ sale_chart.values }}".split("-"),
          sale_chart_labels = "{{ sale_chart.labels }}".split("-"),
          sale_chart_high = parseInt("{{ sale_chart.high|escapejs }}"),
          revenue_chart_values = "{{ revenue_chart.values }}".split("-"),
          revenue_chart_labels = "{{ revenue_chart.labels }}".split("-"),
          revenue_chart_high = parseInt("{{ revenue_chart.high|escapejs }}");
          
    document.getElementById("dailySalesChart").__chartist__.update(
        {
            series: [sale_chart_values],
            labels: sale_chart_labels
        }, {
            high: sale_chart_high,
            chartPadding: {
                top: 6
            }
        }, true);
    document.getElementById("revenueChart").__chartist__.update(
        {
            series: [revenue_chart_values],
            labels: revenue_chart_labels
        }, {
            high: revenue_chart_high,
            chartPadding: {
                top: 4
            }
        }, true);

var $autoPrice = $(".auto-price"),
            $count = $(".item-count"),
            $orderType = $("#newOrderForm input[name=order_type]").filter(":checked"),
            $dinein = $("#new_dinein_info"),
            $orderItemTd = $(".order-item-td"),
            $paid = $(".paid-price");
        for (var j = 0; j < $orderItemTd.length; j++) {
            $($orderItemTd[j]).removeAttr("title");
            var content = $($orderItemTd[j]).find("option").filter(":selected").text();
            $($orderItemTd[j]).attr("data-original-title", `Item: ${content}`);
        }
        $paid.filter((i, e) => { return e.value == 0 }).val(0);
        $count.attr("min", 0);
        $("#order_type-i").prop("checked", true);
        if ($orderType.val() === "d") {
            $dinein.hide();
        }
        var $edit_form,
            $edit_dinein,
            $edit_order_type;
            {% for order in orders %}
                $edit_form = $("#editOrderForm-{{ order.qs.public_uuid }}");
                $edit_dinein = $edit_form.find(".dinein_info");
                $edit_order_type = $edit_form.find("input[name=order_type]");
                if ($edit_order_type.filter(':checked').val() === "d") {
                    $edit_dinein.hide();
                }
                $edit_order_type.change((e) => {
                    $("#dinein_info-{{ order.qs.public_uuid }}").toggle()
                });
            {% endfor %}
        $autoPrice.click((e) => {
                var formNumber = e.currentTarget.id.split("-")[1],
                      formType = e.currentTarget.id.split("-")[0],
                      formId = e.currentTarget.closest("form").id,
                      formUuid = formId.split("-").slice(1).join("-"),
                      $form = $(`#${formId}`),
                      $e = $(`#${e.currentTarget.getAttribute("id")}`),
                      orderId = $(`#${e.currentTarget.getAttribute("id")}`);
                var count,
                    fee,
                    $paidPrice;
                    
                if (formType == "edit_form") {
                    fee = parseInt($(`#edit_form-${formNumber}-fee-${formUuid}`).val());
                    count = parseInt($(`#edit_form-${formNumber}-count-${formUuid}`).val() | 0);
                    $paidPrice = $(`#edit_form-${formNumber}-paid_price-${formUuid}`);
                } else {
                    fee = parseInt($(`#id_form-${formNumber}-fee`).val() | 0);
                    count = parseInt($(`#id_form-${formNumber}-count`).val() | 0);
                    $paidPrice = $(`#id_form-${formNumber}-paid_price`);
                }
                
                $e.prop("checked", (_, v) => {
                    v ? $paidPrice.prop("disabled", true)
                        : $paidPrice.prop("disabled", false);
                    if (v) {
                        $form.find(`.paid-price[name=form-${formNumber}-paid_price]`
                            ).val(parseInt(count * fee) | 0);
                    }
                });
            });
            $count.keyup((e) => {
                if (e.currentTarget.value) {
                    const formNumber = e.currentTarget.id.split("-")[1],
                          formUuid = e.currentTarget.closest("form").id.split("-").slice(1).join("-"),
                          formType = e.currentTarget.id.split("-")[0];
                    var fee,
                        $paidPriceLoc,
                        count;

                    if (formType == "id_form") {
                        fee = parseInt($(`#${e.currentTarget.closest("form").id} #id_form-${formNumber}-fee`).val());
                        $autoPriceLoc = $(`#id_form-${formNumber}-auto_price`);
                        count = parseInt($(`#${e.currentTarget.closest("form").id} #id_form-${formNumber}-count`).val() | 0);
                        $paidPriceLoc = $(`#${e.currentTarget.closest("form").id} #id_form-${formNumber}-paid_price`);
                    } else {
                        fee = parseInt($(`#${e.currentTarget.closest("form"
                        ).getAttribute("id")} #edit_form-${formNumber}-fee-${formUuid}`).val());
                        count = parseInt($(`#${e.currentTarget.closest("form"
                        ).getAttribute("id")} #edit_form-${formNumber}-count-${formUuid}`).val() | 0);
                        $paidPriceLoc = $(`#${e.currentTarget.closest("form"
                        ).getAttribute("id")} #edit_form-${formNumber}-paid_price-${formUuid}`);
                        $autoPriceLoc = $(`#edit_form-${formNumber}-auto_price-${formUuid}`);
                    }
                    $autoPriceLoc.prop("checked", (_, v) => {
                        if (v) {
                            $paidPriceLoc.val(parseInt(count * fee) | 0);
                        }
                    });
                }
            });
            $("#newOrderForm input[name=order_type]").change((e) => {
                $dinein.toggle();
            });

$(".csrfmidd").html(csrf_token_elem);
