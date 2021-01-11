odoo.define('printnode_base.ReportActionManager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');
var core = require('web.core');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var session = require('web.session');

var _t = core._t;


ActionManager.include({

    /**
     * Downloads a PDF report for the given url. It blocks the UI during the
     * report generation and download.
     *
     * @param {string} url
     * @returns {Deferred} resolved when the report has been downloaded ;
     *   rejected if something went wrong during the report generation
     */
    _downloadReport: function (url) {
        var self = this;
        framework.blockUI();
        var def = $.Deferred();
        var type = 'qweb-' + url.split('/')[2];
        var blocked = !session.get_file({
            url: '/report/download',
            data: {
                data: JSON.stringify([url, type]),
            },
            success: def.resolve.bind(def),
            error: function () {
                if (arguments[0].data.name == '418') {
                    self.do_notify(_t('Wow, the report is printed!'), _t('Well, actually it has been just sent to the printer via PrintNode service'), false);
                    def.reject();
                } else {
                    crash_manager.rpc_error.apply(crash_manager, arguments);
                    def.reject();
                }
            },
            complete: framework.unblockUI,
        });
        if (blocked) {
            // AAB: this check should be done in get_file service directly,
            // should not be the concern of the caller (and that way, get_file
            // could return a deferred)
            var message = _t('A popup window with your report was blocked. You ' +
                             'may need to change your browser settings to allow ' +
                             'popup windows for this page.');
            this.do_warn(_t('Warning'), message, true);
        }
        return def;
    },

});
});
