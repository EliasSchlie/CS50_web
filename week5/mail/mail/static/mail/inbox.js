document.addEventListener('DOMContentLoaded', function() {
  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);

  // By default, load the inbox
  load_mailbox('inbox');

  document.querySelector('#compose-form').onsubmit = function(e) {
    e.preventDefault();
    fetch('/emails', {
      method: 'POST',
      body: JSON.stringify({
        recipients: document.querySelector('#compose-recipients').value,
        subject: document.querySelector('#compose-subject').value,
        body: document.querySelector('#compose-body').value
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
      } else {
        console.log(data);
        load_mailbox('sent');
      }
    })
  };
});

function compose_email() {

  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';

}

function load_mailbox(mailbox) {
  
  // Show the mailbox and hide other views
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  // Fetch emails for the mailbox
  fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(data => {
      for (const email of data) {
        const emailDiv = document.createElement('div');
        emailDiv.className = 'email';
        emailDiv.style.border = '1px solid black';
        emailDiv.style.backgroundColor = email.read ? 'gray' : 'white';

        emailDiv.innerHTML = `
          <h3>${email.subject}</h3>
          <p>${email.sender} - ${email.timestamp}</p>
        `;

        // Attach the click event handler
        emailDiv.addEventListener('click', () => {
          handle_email_click(email.id); // or pass the whole email object if needed
        });

        document.querySelector('#emails-view').appendChild(emailDiv);
      }
    });
}

function handle_email_click(email_id) {
  fetch(`/emails/${email_id}`)
    .then(response => response.json())
    .then(data => {
      // Get current user from the disabled compose form field
      const current_user = document.querySelector('#compose-form input[disabled]').value;

      document.querySelector('#emails-view').innerHTML = `
        <h3>${data.subject}</h3>
        <p>${data.sender} - ${data.timestamp}</p>
        <p>${data.body}</p>
      `;
      if (data.sender === current_user) {
        // Don't show archive button for emails you sent
        return;
      }
      const reply_button = document.createElement('button');
      reply_button.innerHTML = 'Reply';
      document.querySelector('#emails-view').appendChild(reply_button);
      reply_button.onclick = () => {
        compose_email();
        document.querySelector('#compose-recipients').value = data.sender;
        document.querySelector('#compose-subject').value = `Re: ${data.subject}`;
        document.querySelector('#compose-body').value = `\n\nOn ${data.timestamp}, ${data.sender} wrote:\n\n${data.body}\n\n`;
      };
      const archive_button = document.createElement('button');
      archive_button.innerHTML = data.archived ? 'Unarchive' : 'Archive';
      document.querySelector('#emails-view').appendChild(archive_button); 
      archive_button.onclick = () => {
        if (archive_button.innerHTML === 'Unarchive') {
          archive_button.innerHTML = 'Archive';
          fetch(`/emails/${email_id}`, {
            method: 'PUT',
            body: JSON.stringify({
              archived: false
            })
          });
        } else {
          archive_button.innerHTML = 'Unarchive';
          fetch(`/emails/${email_id}`, {
            method: 'PUT',
            body: JSON.stringify({
              archived: true
            })
          });
          load_mailbox('inbox');
        }
      };
    });
  fetch(`/emails/${email_id}`, {
    method: 'PUT',
    body: JSON.stringify({
      read: true
    })
  });
}