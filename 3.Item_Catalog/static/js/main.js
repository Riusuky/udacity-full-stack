'use strict';

var ENTER_KEY = 13;
//
// function SetClassModifier(selection, baseClass, modifier) {
//     selection.attr('class', selection.attr('class').replace(new RegExp(`${baseClass}[-\\w]*`), baseClass+modifier));
// }


var CategoryModel = Backbone.Model.extend({
    defaults: {
      name: 'name'
    },

    initialize: function() {
        this.selected = false;
    },

    setSelected: function(selected = true) {
        this.selected = selected;

        this.trigger('change:selected', this);
        this.trigger('change', this);
    }
});

var ItemModel = Backbone.Model.extend({
    defaults: {
        name: 'name',
        description: 'description',
        category_id: 0,
        created_on: 0
    },
});

var CategoryCollection = Backbone.Collection.extend({
    model: CategoryModel,
    url: '/api/category',

    initialize: function() {
        this.on('change:selected', this.onSelectCategory);
    },

    selected: function() {
        return this.find(category => category.selected);
    },

    onSelectCategory: function(category) {
        if(category.selected) {
            if( this.lastSelection && (this.lastSelection != category) ) {
                this.lastSelection.setSelected(false);
            }

            this.lastSelection = category;
        }
        else if(this.lastSelection == category) {
            this.lastSelection = null;
        }
    },

    setUserId: function(userId) {
        this.userId = userId;

        this.trigger('userChanged');
    }
});

var categoryCollection = new CategoryCollection();

var CategoryView = Backbone.View.extend({
    tagName: 'li',
    className: 'menu-list__item',
    template: _.template(
        `<button class="menu-list__delete-button fa fa-trash-o" type="button" name="button"></button>
         <span class="menu-list__text"><%= get('name') %></span>`
    ),

    events: {
        'click': 'onClick',
        'click .menu-list__delete-button': 'deleteCategory'
    },

    initialize: function() {
        this.listenTo(this.model, 'destroy', this.onDestroy);
        this.listenTo(this.model, 'change', this.render);
        this.listenTo(categoryCollection, 'userChanged', this.render);
    },

    deleteCategory: function(event) {
        event.stopPropagation();

        this.model.destroy({
            wait: true,
            error: function(model, response) {
                window.alert('Failed to remove category. Response: '+response.responseText);
            }
        });
    },

    onDestroy:function() {
        this.remove();
        this.off();
    },

    render: function() {
        this.$el.html(this.template(this.model));

        this.$el.toggleClass('selected', this.model.selected);

        this.$('.menu-list__delete-button').toggleClass('hidden', !(categoryCollection.userId && (categoryCollection.userId == this.model.get('owner_id'))));

        return this;
    },

    onClick: function() {
        this.model.setSelected();
    }
});

var CategoryMenuView = Backbone.View.extend({
    el: ".menu-list",

    events: {
    //   'blur .menu-list__input': 'createCategory',
      'keypress .menu-list__input': 'createCategory',
    },

    initialize: function() {
        this.$container = this.$('.menu-list__item-container');
        this.$newCategoryButton = this.$('.menu-list__input');

        this.listenTo(categoryCollection, 'add', this.onAdd);
        this.listenTo(categoryCollection, 'reset', this.onReset);
        this.listenTo(categoryCollection, 'remove', this.onRemove);
    },

    setInputVisibility: function(visible = true) {
        this.$newCategoryButton.parent().toggleClass('hidden', !visible);
    },

    onAdd: function(category) {
        var newCategory = new CategoryView({ model: category });
        this.$container.prepend( newCategory.render().el );
    },

    onReset: function() {
        this.$container.html('');
        categoryCollection.each(this.onAdd, this);
    },

    onRemove: function(terrain) {
        debugger;
    },

    createCategory: function() {
        if ( ((event.type == 'keypress') && (event.which !== ENTER_KEY)) || !this.$newCategoryButton.val().trim() ) {
            return;
        }

        categoryCollection.create(
            {
                name: this.$newCategoryButton.val().trim()
            },
            {
                wait: true,
                error: function(model, response) {
                    window.alert(response.responseText);
                }
            });

        this.$newCategoryButton.val('');
    }
});
