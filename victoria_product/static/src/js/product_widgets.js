odoo.define('victoria_product.product_widgets', function (require) {
"use strict";

var core = require('web.core');
var common = require('web.form_common');
var _t = core._t;
var QWeb = core.qweb;

 var ProductBooleanButton = common.AbstractField.extend({
    className: 'o_stat_info',
    init: function() {
        this._super.apply(this, arguments);
        switch (this.options["terminology1"]) {
            default:
                var terms = typeof this.options["terminology1"] === 'string' ? {} : this.options["terminology1"];
                this.string_true = _t(terms.string_true || "Publish");
                this.hover_true = _t(terms.hover_true || terms.string_false || "Unpublish On Website");
                this.string_false = _t(terms.string_false || "Unpublish");
                this.hover_false = _t(terms.hover_false || terms.string_true || "Publish On Website");
        }
    },
    render_value: function() {
        this._super();
        this.$el.html(QWeb.render("BooleanButton", {widget: this}));
    },
    is_false: function() {
        return false;
    },
});

core.form_widget_registry.add('product_boolean_button', ProductBooleanButton);

/*core.form_tag_registry.add('button', ProductBooleanButton);
*/
return {
    ProductBooleanButton: ProductBooleanButton
};

});
