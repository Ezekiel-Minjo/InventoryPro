// Wait for DOM to be ready
$(document).ready(function () {
  initializeDataTables();

  $("#sidebarToggle").on("click", function () {
    $("#sidebar").toggleClass("show");
  });

  setTimeout(function () {
    $(".alert").fadeOut("slow");
  }, 5000);

  $(".confirm-delete").on("click", function (e) {
    if (!confirm("Are you sure you want to delete this item?")) {
      e.preventDefault();
    }
  });

  $(".format-currency").each(function () {
    const value = parseFloat($(this).text());
    if (!isNaN(value)) {
      $(this).text(
        "KES " +
          value.toLocaleString("en-KE", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })
      );
    }
  });
});

/**
 * Initialize DataTables on all tables with class 'datatable'
 */
function initializeDataTables() {
  if (!$.fn.DataTable) {
    console.log("DataTables library not loaded");
    return;
  }

  $(".datatable").each(function () {
    const $table = $(this);

    // Skip if already initialized
    if ($.fn.DataTable.isDataTable($table)) {
      console.log("DataTable already initialized, skipping");
      return;
    }

    // Check if table has proper structure
    const hasHeader = $table.find("thead tr th").length > 0;
    const hasBody = $table.find("tbody").length > 0;

    if (!hasHeader || !hasBody) {
      console.log(
        "Table missing thead or tbody, skipping DataTable initialization"
      );
      return;
    }

    // Get column count from header
    const headerCols = $table.find("thead tr:first th").length;
    const bodyCols = $table.find("tbody tr:first td").length;

    // Skip if column mismatch and table has data
    if (bodyCols > 0 && headerCols !== bodyCols) {
      console.log(`Column mismatch: Header=${headerCols}, Body=${bodyCols}`);
      return;
    }

    try {
      $table.DataTable({
        pageLength: 25,
        lengthMenu: [
          [10, 25, 50, 100, -1],
          [10, 25, 50, 100, "All"],
        ],
        order: [[0, "desc"]],
        language: {
          search: "Search:",
          lengthMenu: "Show _MENU_ entries",
          info: "Showing _START_ to _END_ of _TOTAL_ entries",
          infoEmpty: "Showing 0 to 0 of 0 entries",
          infoFiltered: "(filtered from _MAX_ total entries)",
          emptyTable: "No data available in table",
          zeroRecords: "No matching records found",
          paginate: {
            first: "First",
            last: "Last",
            next: "Next",
            previous: "Previous",
          },
        },
        responsive: true,
        autoWidth: false,
        dom:
          '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
          '<"row"<"col-sm-12"tr>>' +
          '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
      });

      console.log("DataTable initialized successfully");
    } catch (error) {
      console.error("Error initializing DataTable:", error);
    }
  });
}

/**
 * Reload DataTable (useful for AJAX updates)
 */
function reloadDataTable(tableId) {
  const table = $(tableId).DataTable();
  if (table) {
    table.ajax.reload();
  }
}

/**
 * Format currency values
 */
function formatCurrency(amount) {
  return (
    "KES " +
    parseFloat(amount).toLocaleString("en-KE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  );
}

/**
 * Format phone number
 */
function formatPhoneNumber(phone) {
  // Format to 254XXXXXXXXX
  phone = phone.replace(/\s+/g, "");
  if (phone.startsWith("0")) {
    return "254" + phone.substring(1);
  } else if (phone.startsWith("+")) {
    return phone.substring(1);
  }
  return phone;
}

/**
 * Show loading spinner
 */
function showLoading(message = "Loading...") {
  const html = `
        <div id="loadingOverlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
             background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; 
             justify-content: center;">
            <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>${message}</p>
            </div>
        </div>
    `;
  $("body").append(html);
}

/**
 * Hide loading spinner
 */
function hideLoading() {
  $("#loadingOverlay").remove();
}

/**
 * Show toast notification
 */
function showToast(message, type = "success") {
  const bgColor =
    {
      success: "bg-success",
      error: "bg-danger",
      warning: "bg-warning",
      info: "bg-info",
    }[type] || "bg-primary";

  const html = `
        <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 9999;">
            <div class="toast show ${bgColor} text-white" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>
    `;

  $("body").append(html);

  setTimeout(function () {
    $(".toast-container").fadeOut("slow", function () {
      $(this).remove();
    });
  }, 3000);
}

/**
 * Confirm action with custom message
 */
function confirmAction(message, callback) {
  if (confirm(message)) {
    callback();
  }
}

/**
 * Print element
 */
function printElement(elementId) {
  const printContents = document.getElementById(elementId).innerHTML;
  const originalContents = document.body.innerHTML;

  document.body.innerHTML = printContents;
  window.print();
  document.body.innerHTML = originalContents;
  location.reload();
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(
    function () {
      showToast("Copied to clipboard!", "success");
    },
    function () {
      showToast("Failed to copy", "error");
    }
  );
}

/**
 * Export table to CSV
 */
function exportTableToCSV(tableId, filename = "export.csv") {
  const table = document.getElementById(tableId);
  let csv = [];

  // Get headers
  const headers = [];
  table.querySelectorAll("thead th").forEach((th) => {
    headers.push(th.textContent.trim());
  });
  csv.push(headers.join(","));

  // Get rows
  table.querySelectorAll("tbody tr").forEach((tr) => {
    const row = [];
    tr.querySelectorAll("td").forEach((td) => {
      row.push('"' + td.textContent.trim().replace(/"/g, '""') + '"');
    });
    csv.push(row.join(","));
  });

  // Download
  const csvContent = csv.join("\n");
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}

/**
 * Validate form before submit
 */
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form.checkValidity()) {
    form.reportValidity();
    return false;
  }
  return true;
}

/**
 * AJAX helper function
 */
function ajaxRequest(
  url,
  method = "GET",
  data = null,
  successCallback,
  errorCallback
) {
  $.ajax({
    url: url,
    method: method,
    data: data,
    dataType: "json",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    success: function (response) {
      if (successCallback) successCallback(response);
    },
    error: function (xhr, status, error) {
      if (errorCallback) {
        errorCallback(error);
      } else {
        showToast("An error occurred: " + error, "error");
      }
    },
  });
}

/**
 * Get CSRF token from cookie
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
