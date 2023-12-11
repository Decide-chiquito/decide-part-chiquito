document.addEventListener('DOMContentLoaded', function () {

    document.getElementById('openModalButton').addEventListener('click', function () {
        document.getElementById('myModal').style.display = 'block';
    });

    document.getElementById('closeModalButton').addEventListener('click', function () {
        document.getElementById('myModal').style.display = 'none';
    });

    document.getElementById('id_csv_upload').addEventListener('change', updateFileInfo);

});
