FROM php:7.4-apache

COPY web/ /var/www/html/
COPY flag.txt /var/www/flag.txt

RUN sed -i 's/Listen 80/Listen 8888/' /etc/apache2/ports.conf
RUN sed -i 's/<VirtualHost \*:80>/<VirtualHost \*:8888>/' /etc/apache2/sites-available/000-default.conf

RUN chown -R www-data:www-data /var/www/html && \
    chmod -R 755 /var/www/html && \
    chown www-data:www-data /var/www/flag.txt

EXPOSE 8888
CMD ["apache2-foreground"]
