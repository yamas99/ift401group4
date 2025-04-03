document.addEventListener("DOMContentLoaded", function () {
    var editUserModal = document.getElementById('editUserModal');
    editUserModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;  // Button that triggered the modal
        var userId = button.getAttribute('data-user-id');
        var userName = button.getAttribute('data-user-name');
        var userUsername = button.getAttribute('data-user-username');
        var userEmail = button.getAttribute('data-user-email');
        var userRole = button.getAttribute('data-user-role');

        var form = document.getElementById('editUserForm');
        form.action = '/edit_user/' + userId;

        document.getElementById('editName').value = userName;
        document.getElementById('editUsername').value = userUsername;
        document.getElementById('editEmail').value = userEmail;
        document.getElementById('editRole').value = userRole;
    });
});
