//-------------- API LAYER ---------------//

package com.example.movieactors.movie;

import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping(path = "/api/v1/movies")
public class MovieController {

    private final MovieService movieService;

    public MovieController(MovieService movieService) {
        this.movieService = movieService;
    }

    @GetMapping
    public List<Movie> listMovies() {
        return movieService.getMovies();
    }

    @GetMapping("/movieactors")
    public List<Movie> listMovieActors(){
        return movieService.getMovieActors();
    }

    @GetMapping("{id}")
    public Movie getMovieId(@PathVariable("id") Integer id) {
        return movieService.getMovie(id);
    }

    @PostMapping
    public void addMovie(@RequestBody Movie movie) {
        movieService.addNewMovie(movie);
    }

    @PostMapping("/multiple")
    public void addMultipleMovies(@RequestBody List<Movie> movie) {
        movieService.addManyMovies(movie);
    }

    @DeleteMapping("/delete/{id}")
    public void deleteMovie(@PathVariable("id") Integer id) {
        movieService.deleteMovie(id);
    }

}
