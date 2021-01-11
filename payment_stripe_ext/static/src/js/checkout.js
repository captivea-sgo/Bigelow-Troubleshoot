odoo.define('payment_stripe_ext.FormRenderer', function (require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var BasicRenderer = require('web.BasicRenderer');
var FormRenderer = require('web.FormRenderer');

var _t = core._t;
var qweb = core.qweb;

ajax.loadXML('/payment_stripe_ext/static/src/xml/stripe_templates.xml', qweb);
$.getScript('https://checkout.stripe.com/checkout.js');

FormRenderer.include({
    events: _.extend({}, BasicRenderer.prototype.events, {
        'click #pay_stripe': '_onClickpaystrip',
    }),
    _onClickpaystrip: function(e){
        var handler = StripeCheckout.configure({
            key: $("input[name='stripe_key']").val(),
            image: $("input[name='stripe_image']").val(),
            locale: 'auto',
            closed: function() {
              if (!handler.isTokenGenerate) {
                    $('#pay_stripe')
                        .removeAttr('disabled')
                        .find('i').remove();
              }
            },
            token: function(token, args) {
                handler.isTokenGenerate = true;
                ajax.jsonRpc("/payment/stripe/create_charge", 'call', {
                    tokenid: token.id,
                    email: token.email,
                    token: token,
                    amount: $("input[name='amount']").val(),
                    acquirer_id: $("#acquirer_stripe").val(),
                    currency: $("input[name='currency']").val(),
                    invoice_num: $("input[name='invoice_num']").val(),
                    tx_ref: $("input[name='invoice_num']").val(),
                    return_url: $("input[name='return_url']").val(),
                    is_backend_pay: true,
                }).done(function(data){
                    handler.isTokenGenerate = false;
                    window.location.reload();
                }).fail(function(){
                    var msg = arguments && arguments[1] && arguments[1].data && arguments[1].data.message;
                    var wizard = $(qweb.render('stripe.error', {'msg': msg || _t('Payment error')}));
                    wizard.appendTo($('body')).modal({'keyboard': true});
                });
            },
        });
        if(!$(e.currentTarget).find('i').length)
            $(e.currentTarget).append('<i class="fa fa-spinner fa-spin"/>');
            $(e.currentTarget).attr('disabled','disabled');
        var acquirer_id = $("input[name='acquirer']").val()
        if (! acquirer_id) {
            return false;
        }
        e.preventDefault();
        ajax.jsonRpc('/payment_stripe/transaction', 'call', {
            reference: $("input[name='invoice_num']").val(),
            amount: $("input[name='amount']").val(),
            currency_id: $("input[name='currency_id']").val(),
            partner: $("input[name='partner']").val(),
            acquirer_id: acquirer_id
        })
        handler.open({
            name: $("input[name='merchant']").val(),
            description: $("input[name='invoice_num']").val(),
            currency: $("input[name='currency']").val(),
            email: $("input[name='email']").val(),
            amount: $("input[name='amount']").val()*100,
        });
    },
});
});
