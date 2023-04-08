# Restaurant

A django app that serves restaurants. Something like GrubHub and SnappFood.

![](static/assets/img/doc/Firefox_Screenshot_2023-02-26T16-06-59.539Z.png?raw=true)

This app uses the following technologies:
+ Written in Python
+ Django
+ GeoDjango
+ Django Rest Framework
+ Django Channels
+ Django Allauth
+ Django CMS
+ Django Filters
+ Bootstrap
+ Jquery
+ Javascript
+ Chartist.js
+ Chart.js
+ JWT
+ Redis
+ RabbitMQ
+ Celery
+ Selenium (for tests)
+ Pytest
+ Webpush
+ Elasticsearch
+ Docker
+ PostgreSQL
+ Nginx
+ Git

Currently, because of some issues there's no possibility for deployment because of my uni-enterance exam,
  but soon enough i will deploy it on a server. I apologize for that.
Also, this app is under constant update and maintainance so every once in a while you may see new features in it.
You can have a look at the app. I have provided images of it and they're accessible in 'static/assets/img/doc'.
I also am working on a technical documentation.

---
### TODO:
- [ ] Add the feature for admins to manage their resources and ingrediants. Also, define a new type of user 'supplier' for that.
- [ ] Handle dine-in orders so that waiters can submit orders in real-time (the real time is handled).
- [ ] Handle Drivers and Carriers.
- [ ] Define status_types for orders, so that they're either 'Pending', 'Canceled', 'Ready', or 'Delivered'.
- [ ] Handle Discounts and offs.
- [x] Adding Salary and Payslips and Payments for employees (in development)
- [ ] Adding a celery-beats job for making payslips on the first they of each month for all the employees.
- [ ] Reformat the code.
- [ ] Change the name of the app 'in_place' to 'dine_in'
