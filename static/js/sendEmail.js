function sendMail(contactForm) {
    emailjs.send("gmail", "hmz", {
        "from_name": contactForm.name.value,
        "from_email": contactForm.email.value,
        "query_request": contactForm.message.value
    })
    .then(
        function(response) {
            console.log("SUCCESS", response);
        },
        function(error) {
            console.log("FAILED", error);
        }
    );
    return false;  // To block from loading a new page
}