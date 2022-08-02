from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http.response import HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import datetime

from catalog.models import Book, BookInstance, Author, Genre
from catalog.forms import RenewBookForm


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

class BookListView(LoginRequiredMixin, ListView):
    """Class-Based View for book list."""
    model = Book
    paginate_by = 10
    
class BookDetailView(DetailView):
    """Class-Based View for book detail."""
    model = Book
    
class AuthorListView(ListView):
    """Class-Based View for author list."""
    model = Author
    
class AuthorDetailView(DetailView):
    """Class-Based View for author detail."""
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')
    
class BorrowedBooksListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BookInstance
    template_name = 'catalog/borrowed_books_list.html'
    context_object_name = 'borrowed_bookins'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'
    
    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by( 'borrower')

def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # S'il s'agit d'une requête POST, traiter les données du formulaire.
    if request.method == 'POST':

        # Créer une instance de formulaire et la peupler avec des données récupérées dans la requête (liaison) :
        form = RenewBookForm(request.POST)

        # Vérifier que le formulaire est valide :
        if form.is_valid():
            # Traiter les données dans form.cleaned_data tel que requis (ici on les écrit dans le champ de modèle due_back) :
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # Rediriger vers une nouvelle URL :
            return HttpResponseRedirect(reverse('all-borrowed'))

        # S'il s'agit d'une requête GET (ou toute autre méthode), créer le formulaire par défaut.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)