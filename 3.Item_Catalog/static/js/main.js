'use strict';

// Enter keycode
var ENTER_KEY = 13;

// Models
var CategoryModel = Backbone.Model.extend({
    defaults: {
      name: 'name'
    },

    initialize: function() {
        this.selected = false;
    },

    setSelected: function(selected = true) {
        if(this.selected != selected) {
            this.selected = selected;

            this.trigger('change:selected', this);
            this.trigger('change', this);
        }
    }
});

var ItemModel = Backbone.Model.extend({
    defaults: {
        name: 'name',
        description: 'description',
        category_id: 0
    }
});


// Collections
var CategoryCollection = Backbone.Collection.extend({
    model: CategoryModel,
    url: '/api/category',

    initialize: function() {
        this.on('change:selected', this.onSelectCategory);
    },

    // Returns a selected category
    selected: function() {
        return this.find(category => category.selected);
    },

    // Unselect previous selected category
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

        this.trigger('selectionChanged', category);
    },

    // Sets the current user_id
    setUserId: function(userId) {
        this.userId = userId;

        this.trigger('userChanged');
    },

    // Return all categories for the current user_id
    getByOwner: function() {
        if(this.userId) {
            return this.where({owner_id: this.userId});
        }

        return [];
    },
});

var ItemCollection = Backbone.Collection.extend({
    model: ItemModel,
    url: '/api/item',

    initialize: function() {
        this.comparator = 'created_on';
    }
});

var categoryCollection = new CategoryCollection();
var itemCollection = new ItemCollection();


// Views
// View for a single category
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

    // Delete category from server
    deleteCategory: function(event) {
        event.stopPropagation();

        this.model.destroy({
            wait: true,
            error: function(model, response) {
                window.alert('Failed to remove category. Response: '+response.responseText);
            }
        });
    },

    // Remove category from layout
    onDestroy:function() {
        this.remove();
        this.off();
    },

    // Update element
    render: function() {
        this.$el.html(this.template(this.model));

        this.$el.toggleClass('selected', this.model.selected);

        this.$('.menu-list__delete-button').toggleClass('hidden', !(categoryCollection.userId && (categoryCollection.userId == this.model.get('owner_id'))));

        return this;
    },

    // Select category
    onClick: function() {
        this.model.setSelected(!this.model.selected);
    }
});

// View for a single item
var ItemView = Backbone.View.extend({
    tagName: 'li',
    className: 'item-list__item',
    template: _.template(
        `<h3 class="item-list__item__title"><%= title %></h3>
        <h3 class="item-list__item__category">Category: <%= category %></h3>
        <img class="item-list__item__image" src="<%= imagePath %>">
        <p class="item-list__item__description"><%= description %></p>
        <button class="item-list__item__edit-button fa fa-pencil hidden" type="button"></button>
        <button class="item-list__item__delete-button fa fa-trash-o hidden" type="button"></button>

        <input class="item-list__item__title input" placeholder="Title" type="text" value="<%= title %>">
        <select class="item-list__item__category input">
            <option value="-1" selected>Select a category</option>
        </select>
        <input class="item-list__item__image input" type="image" src="<%= imagePath %>" value="Select image">
        <input class="item-list__item__image-real-input" type="file" value="">
        <textarea class="item-list__item__description input" placeholder="Description"><%= description %></textarea>
        <button class="item-list__item__save-button fa fa-check" type="button"></button>
        <button class="item-list__item__cancel-button fa fa-times" type="button"></button>`
    ),

    categoryOptionTemplate: _.template(
        `<option value="<%= get('id') %>"><%= get('name') %></option>`
    ),

    events: {
        'click .item-list__item__edit-button': 'onEdit',
        'click .item-list__item__delete-button': 'onDelete',
        'click .item-list__item__save-button': 'onSave',
        'click .item-list__item__cancel-button': 'onCancel',
        'click .item-list__item__image.input': 'pickImage',
        'change .item-list__item__image-real-input': 'setImage'
    },

    initialize: function() {
        this.editMode = false;

        if(this.model) {
            this.listenTo(this.model, 'destroy', this.onDestroy);
            this.listenTo(this.model, 'remove', this.onDestroy);
            this.listenTo(this.model, 'change', this.render);
        }

        this.listenTo(categoryCollection, 'userChanged', this.render);
        this.listenTo(categoryCollection, 'add', this.render);
        this.listenTo(categoryCollection, 'reset', this.render);
    },

    // Delete item from server (if it has a model attached)
    onDelete: function(event) {
        event.stopPropagation();

        var imageId = this.model.get('image_id');

        this.model.destroy({
            wait: true,
            error: function(model, response) {
                window.alert('Failed to remove item. Response: '+response.responseText);
            },
            success: function() {
                if(imageId) {
                    $.ajax({
                        type: 'DELETE',
                        url: '/api/image/'+imageId,
                        headers: { 'state': categoryCollection.userState }
                    }).fail(function(error) {
                        window.alert('Failed to delete image attached: '+JSON.stringify(error, undefined, 2));
                    });
                }
            }
        });
    },

    // Change layout to editable mode
    onEdit: function(event) {
        event.stopPropagation();

        this.$titleInput.val(this.model.get('name'));
        this.$descriptionInput.val(this.model.get('description'));
        this.$categoryInput.val(categoryCollection.get(this.model.get('category_id')).get('id'));
        this.$imageInput[0].src = this.model.get('image_url');
        this.imageInputFile = null;

        this.setEditMode(true);
    },

    // Cancel editmode (if it has no model attached, then delete this view)
    onCancel: function(event) {
        event.stopPropagation();

        if(this.model) {
            this.setEditMode(false);
        }
        else {
            this.trigger('destroy');
        }
    },

    setEditMode: function(enable) {
        this.$el.toggleClass('editmode', enable);

        this.editMode = enable;

        if(this.editMode && this.model) {
            this.model.trigger('edit', this.model, this);
        }
    },

    // Update item data on server and refresh element (if it does not have a model attached, then create item)
    onSave: function(event) {
        event.stopPropagation();

        var self = this;

        if(this.editMode) {
            if(this.model) {
                if(this.imageInputFile) {
                    // Updates image and then updates the item and refreshes
                    var formData = new FormData();

                    formData.append('image', this.imageInputFile, this.imageInputFile.name);

                    var imageId = this.model.get('image_id');

                    var requestType = imageId ? 'PATCH' : 'POST'

                    $.ajax({
                        type: requestType,
                        url: '/api/image'+(imageId ? `/${imageId}` : ''),
                        data: formData,
                        processData: false,
                        contentType: false,
                        headers: { 'state': categoryCollection.userState }
                    }).done(function(result) {
                        self.model.save({
                            name: self.$titleInput.val(),
                            description: self.$descriptionInput.val(),
                            category_id: Number(self.$categoryInput.val()),
                            image_id: result.id
                        }, {
                            patch: true,
                            wait: true,
                            error: function(model, response) {
                                window.alert('Failed to edit item. Response: '+response.responseText);
                            },
                            success: function() {
                                self.setEditMode(false);
                                self.model.fetch();
                            }
                        });
                    }).fail(function(error) {
                        window.alert('Failed to upload image: '+JSON.stringify(error, undefined, 2));
                    });
                }
                else {
                    // updates the item on the server
                    this.model.save({
                        name: self.$titleInput.val(),
                        description: self.$descriptionInput.val(),
                        category_id: Number(self.$categoryInput.val())
                    }, {
                        patch: true,
                        wait: true,
                        error: function(model, response) {
                            window.alert('Failed to edit item. Response: '+response.responseText);
                        },
                        success: function() {
                            self.setEditMode(false);
                        }
                    });
                }
            }
            else {
                if(this.imageInputFile) {
                    // Create the image and then the item

                    var formData = new FormData();

                    formData.append('image', this.imageInputFile, this.imageInputFile.name);

                    $.ajax({
                        type: 'POST',
                        url: '/api/image',
                        data: formData,
                        processData: false,
                        contentType: false,
                        headers: { 'state': categoryCollection.userState }
                    }).done(function(result) {
                        itemCollection.create(
                            {
                                name: self.$titleInput.val(),
                                description: self.$descriptionInput.val(),
                                category_id: Number(self.$categoryInput.val()),
                                image_id: result.id
                            },
                            {
                                wait: true,
                                error: function(model, response) {
                                    window.alert('Failed to create item. Response: '+response.responseText);
                                },
                                success: function() {
                                    self.onDestroy();
                                }
                            }
                        );
                    }).fail(function(error) {
                        window.alert('Failed to upload image: '+JSON.stringify(error, undefined, 2));
                    });
                }
                else {
                    itemCollection.create(
                        {
                            name: self.$titleInput.val(),
                            description: self.$descriptionInput.val(),
                            category_id: Number(self.$categoryInput.val())
                        },
                        {
                            wait: true,
                            error: function(model, response) {
                                window.alert('Failed to create item. Response: '+response.responseText);
                            },
                            success: function() {
                                self.onDestroy();
                            }
                        }
                    );
                }
            }
        }
    },

    // Remove element from layout
    onDestroy:function() {
        this.remove();
        this.off();
    },

    // Open image picker
    pickImage: function() {
        this.$fileInput.click();
    },

    // Callback after a image has been selected.
    setImage: function() {
        if(this.$fileInput[0].files.length > 0) {
            var typeIsValid = false;

            var fileTypes = ['image/jpeg', 'image/pjpeg', 'image/png'];

            for(var i = 0; i < fileTypes.length; i++) {
                if(this.$fileInput[0].files[0].type === fileTypes[i]) {
                    typeIsValid = true;
                    break;
                }
            }

            if(typeIsValid) {
                this.imageInputFile = this.$fileInput[0].files[0];

                // Display image preview
                var reader = new FileReader();

                var self = this;

                reader.onload = function (e) {
                    self.$imageInput[0].src = e.target.result;
                }

                reader.readAsDataURL(this.imageInputFile);
            }
            else {
                window.alert('Selected file is not a valid image type.');
            }

            this.$fileInput.val('');
        }
    },

    // Updates element whether it has a model attached or not.
    render: function() {
        if(this.model) {
            var myCategory = categoryCollection.get(this.model.get('category_id'));

            this.$el.html(this.template({
                title: this.model.get('name'),
                description: this.model.get('description'),
                imagePath: this.model.get('image_url'),
                category: myCategory.get('name')
            }));

            this.$titleInput = this.$('.item-list__item__title.input');
            this.$descriptionInput = this.$('.item-list__item__description.input');
            this.$categoryInput = this.$('.item-list__item__category.input');

            this.$imageInput = this.$('.item-list__item__image.input');
            this.$fileInput = this.$('.item-list__item__image-real-input');

            var self = this;

            categoryCollection.getByOwner().forEach(function(category) {
                self.$categoryInput.append(self.categoryOptionTemplate(category));
            });

            this.$categoryInput.val(myCategory.get('id'));

            var enableButtons = (categoryCollection.userId && (categoryCollection.userId == this.model.get('owner_id')));

            if(this.editMode && !enableButtons) {
                self.setEditMode(enableButtons);
            }

            this.$('.item-list__item__edit-button').toggleClass('hidden', !enableButtons);
            this.$('.item-list__item__delete-button').toggleClass('hidden', !enableButtons);
        }
        else if(!categoryCollection.userId) {
            this.onDestroy();
            return null;
        }
        else {
            this.$el.html(this.template({
                title: '',
                description: '',
                imagePath: '',
                category: ''
            }));

            this.$titleInput = this.$('.item-list__item__title.input');
            this.$descriptionInput = this.$('.item-list__item__description.input');
            this.$categoryInput = this.$('.item-list__item__category.input');

            this.$imageInput = this.$('.item-list__item__image.input');
            this.$fileInput = this.$('.item-list__item__image-real-input');

            var self = this;

            categoryCollection.getByOwner().forEach(function(category) {
                self.$categoryInput.append(self.categoryOptionTemplate(category));
            });

            self.setEditMode(true);
        }

        return this;
    },
});


var CategoryMenuView = Backbone.View.extend({
    el: ".menu-list",

    events: {
      'keypress .menu-list__input': 'createCategory',
    },

    initialize: function() {
        this.$container = this.$('.menu-list__item-container');

        this.listenTo(categoryCollection, 'add', this.render);
        this.listenTo(categoryCollection, 'reset', this.render);
        this.listenTo(categoryCollection, 'remove', this.onRemove);

        this.render();
    },

    // Enable/Disable the new category field
    setInputVisibility: function(visible = true) {
        this.$newCategoryButton.parent().toggleClass('hidden', !visible);
    },

    // Add view for new category
    onAdd: function(category) {
        var newCategory = new CategoryView({ model: category });
        this.$container.prepend( newCategory.render().el );
    },

    // Refreshes item collection (deleting an category also deletes all items attached to it)
    onRemove: function(terrain) {
        itemCollection.fetch({
            error: function() {
                window.alert('Failed to fetch items from server');
            }
        });
    },

    // Updates menu element
    render: function() {
        this.$container.find('.menu-list__item').remove();

        this.$newCategoryButton = this.$('.menu-list__input');

        categoryCollection.chain().sortBy(function(category){ return category.get('name'); }).reverse().each(this.onAdd, this);
    },

    // Create a new category on the server
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
                    window.alert('Failed to create category. Response: '+response.responseText);
                }
            }
        );

        this.$newCategoryButton.val('');
    }
});

var ItemListView = Backbone.View.extend({
    el: ".item-list",

    events: {
        'click .item-list__new-item': 'addNewItem'
    },

    initialize: function() {
        this.$container = this.$('.item-list__container');
        this.$listGroupTitle = this.$('.item-list__header-text');
        this.$newItemButton = this.$('.item-list__new-item');

        this.listenTo(itemCollection, 'add', this.render);
        this.listenTo(itemCollection, 'reset', this.render);
        this.listenTo(itemCollection, 'remove', this.render);
        this.listenTo(itemCollection, 'change', this.render);
        this.listenTo(itemCollection, 'edit', this.onEditItem);
        this.listenTo(categoryCollection, 'selectionChanged', this.render);
        this.listenTo(categoryCollection, 'userChanged', this.render);

        this.newItemInput = null;
    },

    // Add view for new item
    addItem: function(category) {
        var newCategory = new ItemView({ model: category });

        this.$container.prepend( newCategory.render().$el );
    },

    // Callback called every time an item starts being edited. (It ensures that only one item is being edited at a time)
    onEditItem: function(item, itemView) {
        if(this.newItemInput) {
            this.cancelNewItem();
        }

        if(itemView != this.lastEditingItem) {
            this.cancelLastEditingItem();
        }

        this.lastEditingItem = itemView;
    },

    // Disable editmode from last item being edited
    cancelLastEditingItem: function() {
        if(this.lastEditingItem && this.lastEditingItem.editMode) {
            this.lastEditingItem.setEditMode(false);

            this.lastEditingItem = null;
        }
    },

    // Update item list element
    render: function() {
        var selectedCategory = categoryCollection.selected();

        this.$container.find('.item-list__item').remove();

        var enableNewItemButton = false;

        if(selectedCategory) {
            this.$listGroupTitle.text(selectedCategory.get('name'));

            _.chain(itemCollection.where({ category_id: selectedCategory.get('id') }))
                .sortBy(function(item){ return item.get('created_on'); })
                .each(this.addItem, this);

            enableNewItemButton = (categoryCollection.userId && (categoryCollection.userId == selectedCategory.get('owner_id')));
        }
        else {
            this.$listGroupTitle.text('Recent Items');

            itemCollection.slice(0, 10).forEach(this.addItem.bind(this));

            enableNewItemButton = categoryCollection.userId;
        }

        if(this.newItemInput && !categoryCollection.userId) {
            this.newItemInput.onDestroy();
            this.newItemInput = null;
        }

        this.$newItemButton.toggleClass('hidden', !enableNewItemButton && !this.newItemInput);
    },

    // Creates the form fom a new item
    addNewItem: function() {
        this.newItemInput = new ItemView();

        this.listenTo(this.newItemInput, 'destroy', this.cancelNewItem);

        this.$container.append( this.newItemInput.render().$el );

        this.$newItemButton.toggleClass('hidden', true);

        this.cancelLastEditingItem();
    },

    // Deletes form for new item if it exists
    cancelNewItem: function() {
        if(this.newItemInput) {
            this.stopListening(this.newItemInput);

            this.newItemInput.onDestroy();

            this.newItemInput = null;

            this.$newItemButton.toggleClass('hidden', false);
        }
    }
});
