const { Client } = require('whatsapp-web.js');


const client = new Client();
const qrcode = require('qrcode-terminal')

// When the client is ready, run this code (only once)
client.once('ready', () => {
    console.log('Client is ready!');
});

// When the client received QR-Code
client.on('qr', (qr) => {
    console.log('QR RECEIVED', qr);
     qrcode.generate(qr, {small: true});
});

// Start your client
client.initialize();

// Listening to all incoming messages
client.on('message_create', message => {
	console.log(message.body);
});

client.on('message_create', message => {
    greeting = 
    "Welcome to sherlock\n I am your virtual assistant and this is what you can do with me: \n 1. Find Lecturer's phone numbers by searching for their name. \n 2. Add Lecturers details(first name, last name and phone number) so that others can find them."
	if (message.body === 'Hello') {
		// send back "pong" to the chat the message was sent in
		client.sendMessage(message.from, greeting);
	}
});


