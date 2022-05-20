package com.example.movieactors.movie;

import com.example.movieactors.actor.Actor;

import java.time.LocalDate;
import java.util.List;

public record Movie(Integer id, // record automatically generates constructor and getter setters
        String name,
        List<Actor> actors,
        LocalDate releaseDate) {
}
